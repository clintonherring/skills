Runbook¶
Runbooks are a useful tool to describe the purpose of a particular application or service, any dependencies of that application or service, as well as other useful information to assist with the operation of the service in production.

All runbooks MUST:

Be linked to via Backstage (recorded in metadata)
Be hosted somewhere that is generally accessible to engineers (recommended either in the code repo or in Confluence)
Describe the application's purpose and the expected business impact if it fails
Describe all internal (JET hosted) dependencies - Name of dependency - How communication with dependencies is implemented (HTTP, Async Messaging) - Timeouts for calls to dependencies for synchronous operations - Justification for timeout values
Describe all external (AWS, Aiven, other 3rd parties) dependencies - Name of dependency (provider and service used) - How communication with dependencies is implemented (HTTP, Async Messaging) - Timeouts for calls to dependencies for synchronous operations - Justification for timeout values
Provide valid links to: - Monitoring dashboards for the application - Linked logging queries for significant events (i.e abnormal status codes, error level application logs) - Alert configuration(s) for the application - Health checks for the application and retry policies. - Backstage - If PlatformMetadata has been completed as expected, backstage will have the links to code repositories, deployment pipelines. (See Platform Metadata section below)
All runbooks SHOULD:

Provide details of known issues with any workarounds.
Use the following template: - General Runbook Template