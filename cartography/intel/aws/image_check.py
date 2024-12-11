import boto3
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ECRCrossCheck:
    def __init__(self, aws_region: str):
        self.ecr_client = boto3.client('ecr', region_name=aws_region)
        self.ecs_client = boto3.client('ecs', region_name=aws_region)
        self.eks_client = boto3.client('eks', region_name=aws_region)
        self.ec2_client = boto3.client('ec2', region_name=aws_region)

    def get_ecr_images(self, repository_name: str) -> List[str]:
        response = self.ecr_client.list_images(repositoryName=repository_name)
        image_ids = response['imageIds']
        return [image['imageDigest'] for image in image_ids]

    def check_image_in_ecs(self, image_digest: str) -> bool:
        clusters = self.ecs_client.list_clusters()['clusterArns']
        for cluster in clusters:
            tasks = self.ecs_client.list_tasks(cluster=cluster)['taskArns']
            for task in tasks:
                task_desc = self.ecs_client.describe_tasks(cluster=cluster, tasks=[task])['tasks']
                for container in task_desc[0]['containers']:
                    if image_digest in container['image']:
                        return True
        return False

    def check_image_in_eks(self, image_digest: str) -> bool:
        clusters = self.eks_client.list_clusters()['clusters']
        for cluster in clusters:
            nodegroups = self.eks_client.list_nodegroups(clusterName=cluster)['nodegroups']
            for nodegroup in nodegroups:
                nodegroup_desc = self.eks_client.describe_nodegroup(clusterName=cluster, nodegroupName=nodegroup)['nodegroup']
                for image in nodegroup_desc['amiType']:
                    if image_digest in image:
                        return True
        return False

    def check_image_in_ec2(self, image_digest: str) -> bool:
        instances = self.ec2_client.describe_instances()['Reservations']
        for reservation in instances:
            for instance in reservation['Instances']:
                if 'ImageId' in instance and image_digest in instance['ImageId']:
                    return True
        return False

    def cross_check_images(self, repository_name: str) -> Dict[str, bool]:
        image_digests = self.get_ecr_images(repository_name)
        results = {}
        for image_digest in image_digests:
            in_ecs = self.check_image_in_ecs(image_digest)
            in_eks = self.check_image_in_eks(image_digest)
            in_ec2 = self.check_image_in_ec2(image_digest)
            results[image_digest] = in_ecs or in_eks or in_ec2
            logger.info(f'Image {image_digest} in use: {results[image_digest]}')
        return results

def main():
    aws_region = 'us-west-2'
    repository_name = 'your-ecr-repository'
    cross_checker = ECRCrossCheck(aws_region)
    results = cross_checker.cross_check_images(repository_name)
    for image_digest, in_use in results.items():
        if in_use:
            logger.info(f'Image {image_digest} is in use.')
        else:
            logger.warning(f'Image {image_digest} is not in use.')

if __name__ == '__main__':
    main()