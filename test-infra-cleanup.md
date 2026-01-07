# Test Infrastructure Cleanup

AWS Profile: `AdministratorAccess-205930638578`
Region: `us-east-1`

## Resources Created (delete in reverse order)

### Listeners
```bash
# Delete listener on target ALB
AWS_PROFILE=AdministratorAccess-205930638578 aws elbv2 delete-listener \
  --listener-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:listener/app/cartography-test-target-alb/d01278641c883064/0845fa3acff5a97f"

# Delete Lambda listener on outpost-testbed-alb
AWS_PROFILE=AdministratorAccess-205930638578 aws elbv2 delete-listener \
  --listener-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:listener/app/outpost-testbed-alb/2907a93e18ab97d3/d12387b98c413427"
```

### Target Groups
```bash
# Delete Lambda target group
AWS_PROFILE=AdministratorAccess-205930638578 aws elbv2 delete-target-group \
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:targetgroup/cartography-test-lambda-tg/81c85888e321586f"

# Delete backend target group (for target ALB)
AWS_PROFILE=AdministratorAccess-205930638578 aws elbv2 delete-target-group \
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:targetgroup/cartography-test-backend-tg/afaab8f8630d247f"

# Delete ALB target group (to be created)
# AWS_PROFILE=AdministratorAccess-205930638578 aws elbv2 delete-target-group \
#   --target-group-arn "<ALB_TG_ARN>"
```

### Load Balancers
```bash
# Delete target ALB (used for ALB-to-ALB chaining)
AWS_PROFILE=AdministratorAccess-205930638578 aws elbv2 delete-load-balancer \
  --load-balancer-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:loadbalancer/app/cartography-test-target-alb/d01278641c883064"
```

### Lambda
```bash
# Delete Lambda function
AWS_PROFILE=AdministratorAccess-205930638578 aws lambda delete-function \
  --function-name cartography-test-lambda

# Delete IAM role
AWS_PROFILE=AdministratorAccess-205930638578 aws iam delete-role \
  --role-name cartography-test-lambda-role
```

## Quick Cleanup Script
```bash
#!/bin/bash
export AWS_PROFILE=AdministratorAccess-205930638578

# Delete listeners first
aws elbv2 delete-listener --listener-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:listener/app/cartography-test-target-alb/d01278641c883064/0845fa3acff5a97f" 2>/dev/null
aws elbv2 delete-listener --listener-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:listener/app/outpost-testbed-alb/2907a93e18ab97d3/d12387b98c413427" 2>/dev/null

# Delete target groups
aws elbv2 delete-target-group --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:targetgroup/cartography-test-lambda-tg/81c85888e321586f" 2>/dev/null
aws elbv2 delete-target-group --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:targetgroup/cartography-test-backend-tg/afaab8f8630d247f" 2>/dev/null

# Delete load balancer
aws elbv2 delete-load-balancer --load-balancer-arn "arn:aws:elasticloadbalancing:us-east-1:205930638578:loadbalancer/app/cartography-test-target-alb/d01278641c883064" 2>/dev/null

# Delete Lambda
aws lambda delete-function --function-name cartography-test-lambda 2>/dev/null

# Delete IAM role
aws iam delete-role --role-name cartography-test-lambda-role 2>/dev/null

echo "Cleanup complete!"
```
