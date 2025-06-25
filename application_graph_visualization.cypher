-- 🎯 COMPLETE APPLICATION ECOSYSTEM VIEW
-- Shows all applications with their users, groups, and tenant relationships
MATCH (tenant:EntraTenant)-[:RESOURCE]->(app:EntraApplication)
OPTIONAL MATCH (user:EntraUser)-[ur:HAS_APP_ROLE]->(app)
OPTIONAL MATCH (group:EntraGroup)-[gr:HAS_APP_ROLE]->(app)
RETURN tenant, app, user, group, ur, gr
LIMIT 100;

-- 📱 FOCUS ON SPECIFIC APPLICATION
-- Replace 'Finance Tracker' with your application name
MATCH (app:EntraApplication {display_name: 'Finance Tracker'})
OPTIONAL MATCH (tenant:EntraTenant)-[:RESOURCE]->(app)
OPTIONAL MATCH (user:EntraUser)-[ur:HAS_APP_ROLE]->(app)
OPTIONAL MATCH (group:EntraGroup)-[gr:HAS_APP_ROLE]->(app)
RETURN tenant, app, user, group, ur, gr;

-- 👥 USER-CENTRIC VIEW
-- Shows a specific user and all their application access
MATCH (user:EntraUser {display_name: 'Test User 1'})
OPTIONAL MATCH (user)-[r:HAS_APP_ROLE]->(app:EntraApplication)
OPTIONAL MATCH (tenant:EntraTenant)-[:RESOURCE]->(app)
RETURN user, r, app, tenant;

-- 🏢 GROUP-CENTRIC VIEW  
-- Shows a specific group and all applications it has access to
MATCH (group:EntraGroup {display_name: 'Finance Team'})
OPTIONAL MATCH (group)-[r:HAS_APP_ROLE]->(app:EntraApplication)
OPTIONAL MATCH (tenant:EntraTenant)-[:RESOURCE]->(app)
RETURN group, r, app, tenant;

-- 🌐 TENANT OVERVIEW
-- Shows all applications under a tenant with their access patterns
MATCH (tenant:EntraTenant)-[:RESOURCE]->(app:EntraApplication)
OPTIONAL MATCH (principal)-[r:HAS_APP_ROLE]->(app)
WHERE principal:EntraUser OR principal:EntraGroup
RETURN tenant, app, principal, r
LIMIT 50;

-- 🔥 MOST CONNECTED APPLICATIONS
-- Shows applications with the most relationships (highly accessed)
MATCH (app:EntraApplication)
WITH app, size((app)<-[:HAS_APP_ROLE]-()) as connection_count
WHERE connection_count > 0
ORDER BY connection_count DESC
LIMIT 10
MATCH (app)
OPTIONAL MATCH (tenant:EntraTenant)-[:RESOURCE]->(app)
OPTIONAL MATCH (principal)-[r:HAS_APP_ROLE]->(app)
RETURN app, tenant, principal, r;

-- 🚫 ISOLATED APPLICATIONS
-- Shows applications with no user/group assignments
MATCH (tenant:EntraTenant)-[:RESOURCE]->(app:EntraApplication)
WHERE NOT (app)<-[:HAS_APP_ROLE]-()
RETURN tenant, app;

-- 🎭 ACCESS PATTERNS BY TYPE
-- Shows the relationship patterns between different node types
MATCH (app:EntraApplication)
OPTIONAL MATCH (tenant:EntraTenant)-[tr:RESOURCE]->(app)
OPTIONAL MATCH (user:EntraUser)-[ur:HAS_APP_ROLE]->(app)  
OPTIONAL MATCH (group:EntraGroup)-[gr:HAS_APP_ROLE]->(app)
RETURN app, tenant, user, group, tr, ur, gr
LIMIT 25;

-- 🔍 SECURITY AUDIT VIEW
-- Shows potential over-privileged access (users/groups with many app assignments)
MATCH (principal)-[r:HAS_APP_ROLE]->(app:EntraApplication)
WHERE principal:EntraUser OR principal:EntraGroup
WITH principal, collect(app) as apps, count(r) as app_count
WHERE app_count >= 2  // Adjust threshold as needed
UNWIND apps as app
MATCH (principal)-[r:HAS_APP_ROLE]->(app)
OPTIONAL MATCH (tenant:EntraTenant)-[:RESOURCE]->(app)
RETURN principal, r, app, tenant;

-- 🌟 INTERACTIVE START POINT
-- Simple query to start exploring - shows a few of each node type
MATCH (tenant:EntraTenant)-[:RESOURCE]->(app:EntraApplication)
WITH tenant, app LIMIT 3
OPTIONAL MATCH (user:EntraUser)-[ur:HAS_APP_ROLE]->(app)
WITH tenant, app, user, ur LIMIT 5
OPTIONAL MATCH (group:EntraGroup)-[gr:HAS_APP_ROLE]->(app)  
RETURN tenant, app, user, group, ur, gr
LIMIT 10; 