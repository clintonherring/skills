
_This is a template for feature RUNBOOKs. Please remove any non-applicable sections and text with an italic font style and replace any placeholders in curly brackets (`{`, `}`). This template should be used as a starting point._

<!---------------------------------------------->
# {Feature Name}


<!---------------------------------------------->
## Summary

{_Description of the feature. Why does this feature matter? What's the core functionality? What does it provide to users?  **What is the impact if stops working?**_} 


| Tier          | Markets                          | Score Card            | CI/CD            | Support#                  |
| ------------- | -------------------------------- | --------------------- | ---------------- | ------------------------- |  
| `{1,2,3}` | `{UK,NL,DE,i18N,etc}`  | [![Score Card](#)](#) | [![Build](#)](#) | [![Support Channel](#)](#)| 


_This is an example of the links structure to be used above:_

[![Score Card](https://scorekeeper.eu-west-1.production.jet-internal.com/api/features/global/{feature}/badge)](https://backstage.eu-west-1.production.jet-internal.com/catalog/default/component/{feature}/scorecard)

[![GHA Build](https://github.je-labs.com/{OWNER}/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/badge.svg)](https://github.com/{OWNER}/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE})

[![Support Channel](https://img.shields.io/badge/slack-<channel--Name--here>-green?style=flat-square&amp;logo=slack)](https://justeat.slack.com/app_redirect?channel=<channelName>)


<!---------------------------------------------->
## Monitoring

_Use this section to provide quick links for logs and metric dashboards. Remove columns which are not applicable to your feature. These links should be a starting point for the engineer so they can quickly jump into metrics and logs that are only for your feature._

| Environment        | Feature Logs | Feature Metrics |
| ------------------ | :----------: | :-------------: |
| {Environment Name} | [Datadog](#)  | [Datadog](#)    |


<!---------------------------------------------->
## Alerts

| Environment   | DD Monitor/Prometheus      | Infra       | 
| ------------- | ------------    | ----------- | 
| {Prod, QA, .} | [Config Link](#link-to-prometheus-or-ddmonitors) | [Alerts](#link-to-infrastructure-alerts) | 

<!---------------------------------------------->
## Useful Links

- [Code Repository](#link-to-code-repository)
- [Infrastructure Repository](#link-to-infrastructure-repository)
- [Backstage](#link-to-feature-on-backstage)
- [Datadog Dashboard](#link-to-feature-datadog-dashboard)
- [Deployment Pipeline](#link-to-feature-on-sonic-or-githubactions)
- [Platform Metadata Definition](#link-to-feature-platform-metadata-entry)
- [Architecture/Solution Specification Document](#link-to-any-documentation-with-more-in-depth-architecture-details)


<!---------------------------------------------->
## PagerDuty
  - [Escalation policy](#link-to-pager-duty-escalation-policy)
  - [Schedule](#link-to-pager-duty-schedule)


<!---------------------------------------------->
## Scalability
`{Inform the Auto scaling process. Is it horizontable scalable? Does it scale up for Load Tests? If any dependencies, does it scale along with compute or other internal depedencies? Add links to the autoscaling configuration}`


<!---------------------------------------------->
## Dependencies

### Data Stores

_Use this section to state what data stores your feature reads or writes to. If your feature does not utilise any data stores then this section can be removed._

_If the data store's name doesn't contain the environment or tenant, for the sake of brevity use placeholders e.g. `[environment]` or `[tenant]`._

| Name                   | Type   | Description                            | Authoritative       | Backed Up           |
| ---------------------- | ------ | -------------------------------------- | :-----------------: | :-----------------: |
| `{Name of data store}` | {Type} | {Describe how this data store is used} | {**Yes** or **No**} | {**Yes** or **No**} |

### APIs

_Use this section to state what APIs and components your feature interacts with. If your feature does not consume any APIs then this section can be removed._

| Service                             | Scope                     | Description                   | Retries                    | Timeout                     |
| ----------------------------------- | ------------------------- | ----------------------------  | :------------------------: | :-------------------------: |
| [Feature Name](#link-to-backstage)  | `{Internal,External,AWS}` | {how and why the svc is used} | {nº of retries in failure} | {waiting time for svc resp} |

### Events

_Use this section to state what events we consume and how we consume them. If your feature does not consume any events then this section can be removed.If your feature publishes any message, list them, otherwise it can be ignored_

| Message Bus     | Message Type | Event         | Description         | Using Queue           | Replayable           |
| --------------- | ------------ | ------------- | ------------------- | :-------------------: | :------------------: |
| `{Sns, Kafka,.}`| `{Type}`     | `{Event Name}`| `{Evt Description}` | `{**Yes** or **No**}` | `{**Yes** or **No**}`|

<!---------------------------------------------->
## Interface

### Events

_If your feature emits events, then use this section to state what events you produce and when and why they are produced. If your feature does not emit any events, then this section can be removed._

| Event Name     | Description                     | Contract                                       | In Big Query        |
| -------------- | ------------------------------- | ---------------------------------------------- | :-----------------: |
| `{Event Name}` | {Describe what the event means} | [Link to C# type or contract documentation](#) | {**Yes** or **No**} |

All events available in Big Query can found in an event table with format `just-data.production_je_justsaying.[event]_[tenant]_[year]`.

### APIs

_If your feature exposes an API, then use this section to state what endpoints you produce and a quick overview of what they do. If your feature does not expose an API, then this section can be removed._

#### Base URI

| Environment          | Host                                    |
| -------------------- | --------------------------------------- |
| `{Environment Name}` | {The API Base URL For That Environment} |

The correct domain shall be returned from `Generate-Configs.ps1` and `generate-configs-js`.

#### Endpoints

| Endpoint          | Method                 | SLA      | Description                      | Behind Smart Gateway | Documentation                             |
| ----------------- | :--------------------: | -------- | -------------------------------- | :------------------: | ----------------------------------------- |
| `{Endpoint Path}` | {Endpoint HTTP Method} | `{99.9%}`| Describe what the endpoint does. | {**Yes** or **No**}  | [Link to API Specification or Swagger](#) |


<!---------------------------------------------->
## Handlers
_If there is any Handler, include the handler name and description._


<!---------------------------------------------->
## Known Scenarios

_Some error scenarios may not be as simple as replay a message. There may be steps involved to determine what the correct course of action is and what to do to validate that impact has been resolved. If you have such scenarios, use the sub-sections below document them. If you feature doesn't have such scenarios, then this section can be removed._

### Possible Issues
_Error scenarios. What should be done if it happens. Potential impact. What log msg is thrown when it happens._

### Feature Flags
_Feature flags that is used by the feature and what it does when enabled/disabled._

### Running it manually
_If required to run it manually, what would be the steps._

### {Other Scenarios: Any other scenario you may find important}
_Details here._


<!---------------------------------------------->
## Troubleshooting Guides

### Alerts How To

| Stage                 | Alert             | Reason               | Resolution     |
| --------------------- | ----------------- | :------------------: | :------------: |
| `{Function Error}`    | `{When it fires}` | `{Possible Reasons}` | `{What to do}` |
| `{Function Throttle}` | `{When it fires}` | `{Possible Reasons}` | `{What to do}` |
| `{Error queue}`       | `{When it fires}` | `{Possible Reasons}` | `{What to do}` |
| `{others}`            | `{When it fires}` | `{Possible Reasons}` | `{What to do}` |

{_If there is any additional HowTo instructions you may find important to support this feature, please add the instructions here._}


<!---------------------------------------------->
## Testing

### Feature testing
_If there is any unit test, data access tests, end to end tests, that are run as part of the solution, please share the test project details, including repositories, etc._

### Load testing
_If the feature is tested as part of the daily production load test, inform the test repository, details, day of the week and time that it takes place. if it's not part of the LT, please share if there is a plan to do so_


<!---------------------------------------------->
## Health Checks

_If your feature has health checks, please describe them. If you feature doesn't have such scenarios, then this section can be removed._

| URL                 | Interval          | What it does?        | What it validates? |
| ------------------- | ----------------- | :------------------: | :----------------: |
| `{url}`             | `{Seconds}`       | `{Description}`      | `{Description}`    |


{_Additional Comments if required_}

<!---------------------------------------------->
## Security

_If you feature doesn't have such scenarios, then this section can be removed, otherwise, please provide the answers for to what applies._

 - Security Groups Configuration: `{link}`
 - Security Groups are locked down to office locations and upstream features: `{yes, no}`
 - List of public endpoints available (e.g. SmartGateway): `{endpoints or link to config file}`
 - This feature processes, stores or transmist CC data: `{Yes and is PCI-DSS compliant | Yes and is not PCI-DSS compliant | No}`
 - This feature processes personal identifiable information: `{Yes and is GDPR compliant | Yes and is not GDPR compliant | No}`
 - This feature stores personal identifiable information: `{Yes and is GDPR compliant | Yes and is not GDPR compliant | No}`
 - Access to this service is granted via: `{local login, Okta, ADFS, etc}`

 
<!---------------------------------------------->
## Disaster Recovery

### Feature Recovery
_Describe (or share the link of) documented steps to restore the feature in a DR scenario (from code/github/scripts/etc)._

### Data Backup
_Describe the impact if all the data is lost_
_Is your data authoritative - can you get it from somewhere else?_
_If the data is available somewhere else - how would you recreate your data and how long would it take? Is this acceptable?_
_How much data can you afford to use (ie how often should you back up)?  Is last night’s data good enough?_

### Authoritative Data Recovery
_If your feature is responsible for authoritative data stores, then use this section to document the data store backup and restoration jobs. If your feature is not responsible for authoritative data, then this section can be removed._

| Environment          | Data Store             | Backup Job    | Restoration Job |
| -------------------- | ---------------------- | :-----------: | :-------------: |
| `{Environment Name}` | `{Name of data store}` | [Link](#)     | [Link](#)       |

### Projection Rebuilding

_If your feature builds a projection, then use this section to document the steps to rebuild/reseed the projection in the event that the projection being wiped out or is out of sync. If your feature does not make use of a projection, then this section can be removed._

| Name          | Type                  | Rebuilding instructions |
| ------------- | --------------------- | :---------------------: |
| `{Proj Name}` | `{DynamoDb, S3, etc}` | `{Description}`         |


<!---------------------------------------------->
## Rollout / Rollback Requirements

{_If your feature has any special rollout/rollback requirements, please add the details of any migration or rollout plan here._}
{_If your feature has a traffic flow, please add it in here}