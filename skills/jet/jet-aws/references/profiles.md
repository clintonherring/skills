# AWS Profile Registry

Complete registry of all configured AWS profiles. All profiles use `eu-west-1` as SSO region.

## Quick Lookup

Search this file by:
- Profile name: `## <section>` then scan the table
- Account ID: search for the numeric ID directly
- Role name: search for the role (e.g., `admin`, `cloudops-platform-user`)

---

## SRE Accounts

Core SRE infrastructure accounts on the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `default` / `sre-dev-1` | 929724455131 | eu-west-1 | admin | SRE dev environment |
| `sre-eks-dev-1` | 470500219165 | eu-west-1 | admin | SRE EKS dev |
| `sre-eks-staging-1` | 472133190586 | eu-west-1 | admin | SRE EKS staging |
| `sre-eks-intsvc-1` | 568184606770 | eu-west-1 | admin | SRE EKS internal services |
| `sre-eks-production-1` | 318528612368 | eu-west-1 | admin | SRE EKS production |
| `sre-eks-gitlab-1` | 806785595086 | eu-west-1 | admin | SRE EKS GitLab runners |
| `sre-commons-staging-1` | 687641532108 | eu-west-1 | admin | SRE commons staging |
| `sre-commons-production-1` | 938705830314 | eu-west-1 | admin | SRE commons production |
| `sre-marathon-staging-1` | 206593080443 | eu-west-1 | admin | SRE marathon staging |
| `sre-marathon-production-1` | 077535881880 | eu-west-1 | admin | SRE marathon production |
| `sre-payouts-recovery` | 645140731321 | eu-west-1 | admin | Payouts recovery |

## CloudOps / Legacy EKS Accounts

Legacy CloudOps and Takeaway platform accounts on the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `cloudops-dev` | 149679936287 | eu-west-1 | admin | CloudOps dev (also QA for EU1) |
| `eks-cluster-dev` | 149679936287 | eu-west-1 | eks | Legacy EKS dev (eks role) |
| `eks-cluster-dev-eks` | 149679936287 | eu-west-1 | cloudops-platform-user | Legacy EKS dev (kubectl) |
| `takeaway` | 790487183666 | eu-west-1 | admin | Takeaway main |
| `takeaway-staging` / `euw1-pdv-stg-5` | 917668556676 | eu-west-1 | admin | Takeaway staging |
| `takeaway-staging-eks` | 917668556676 | eu-west-1 | cloudops-platform-user | Legacy EKS staging (kubectl) |
| `takeaway-production` / `euw1-pdv-prd-5` | 868502343283 | eu-west-1 | admin | Takeaway production |
| `takeaway-production-eks` | 868502343283 | eu-west-1 | cloudops-platform-user | Legacy EKS prod (kubectl) |
| `takeaway-frontend-staging` | 605382523909 | eu-west-1 | admin | Frontend staging |
| `takeaway-frontend-production` | 739804623288 | eu-west-1 | admin | Frontend production |
| `orga` | 778305418618 | eu-west-1 | orga-limited-admin | Organisation/root account |

## PCIT Accounts

Platform CI/CD tooling on the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `pcit-staging` | 917668556676 | eu-west-1 | admin | PCIT staging |
| `pcit-production` | 868502343283 | eu-west-1 | admin | PCIT production |

## OneEKS / Sonic Runtime — EU (eu-west-1)

Sonic Runtime platform delivery, platform, and platform management accounts on the **orga** portal.

### Platform Delivery (pdv)

| Profile | Account ID | Region | Role | Bulkhead | Env |
|---------|-----------|--------|------|----------|-----|
| `euw1-pdv-sbx-2` | 211125636821 | eu-west-1 | admin | - | Sandbox |
| `euw1-pdv-qa-2` | 149679936287 | eu-west-1 | admin | EU1 | QA |
| `euw1-pdv-qa-3` | 891377069564 | eu-west-1 | admin | EU2 | QA |
| `euw1-pdv-stg-5` | 917668556676 | eu-west-1 | admin | EU1 | Staging |
| `euw1-pdv-stg-6` | 851725494124 | eu-west-1 | admin | EU2 | Staging |
| `euw1-pdv-prd-5` | 868502343283 | eu-west-1 | admin | EU1 | Production |
| `euw1-pdv-prd-6` | 654654467576 | eu-west-1 | admin | EU2 | Production |

### Platform (plt)

| Profile | Account ID | Region | Role | Env |
|---------|-----------|--------|------|-----|
| `euw1-plt-stg-2` | 851725319446 | eu-west-1 | admin | Staging |
| `euw1-plt-prd-2` | 058264529639 | eu-west-1 | admin | Production |

### Platform Management (pmt)

| Profile | Account ID | Region | Role | Env |
|---------|-----------|--------|------|-----|
| `euw1-pmt-stg-1` | 043449893185 | eu-west-1 | admin | Staging |
| `euw1-pmt-prd-1` | 674832384991 | eu-west-1 | admin | Production |

## OneEKS / Sonic Runtime — EU Central (eu-central-1)

On the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `p-ec1-commons` | 040568216069 | eu-central-1 | admin | Commons (eu-central-1) |
| `p-ec1-marathon` | 848822256553 | eu-central-1 | admin | Marathon (eu-central-1) |
| `p-ec1-eks` | 498122695664 | eu-central-1 | admin | EKS (eu-central-1) |

## OneEKS / Sonic Runtime — APAC (ap-southeast-2)

On the **orga** portal. Bulkhead: OC1.

| Profile | Account ID | Region | Role | Env |
|---------|-----------|--------|------|-----|
| `apse2-pdv-qa-2` | 992382780937 | ap-southeast-2 | admin | QA |
| `apse2-pdv-stg-2` | 581114218460 | ap-southeast-2 | admin | Staging |
| `apse2-pdv-prd-3` | 901113000551 | ap-southeast-2 | admin | Production |
| `apse2-pmt-stg-1` | 024345218262 | ap-southeast-2 | admin | PMT Staging |
| `apse2-pmt-prd-1` | 576596237931 | ap-southeast-2 | admin | PMT Production |
| `apse2-plt-prd-1` | 654654425804 | ap-southeast-2 | admin | PLT Production |

## OneEKS / Sonic Runtime — US West (us-west-2)

On the **orga** portal. Bulkhead: NA1.

| Profile | Account ID | Region | Role | Env |
|---------|-----------|--------|------|-----|
| `usw2-pdv-qa-1` | 242031136599 | us-west-2 | admin | QA |
| `usw2-pdv-stg-1` | 891377176256 | us-west-2 | admin | Staging |
| `usw2-pdv-prd-2` | 992382718146 | us-west-2 | admin | Production |
| `usw2-plt-prd-2` | 471112928224 | us-west-2 | admin | PLT Production |

## JetConnect / Flyt Accounts

Legacy Just Eat accounts on the **acas** portal (`https://acas.awsapps.com/start`).

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `flyt-management-production` | 746238309645 | eu-west-1 | je-read-write | Flyt management |
| `flyt-staging` | 364123201955 | eu-west-1 | je-read-write | Flyt staging |
| `flyt-production` | 470025225193 | eu-west-1 | je-read-write | Flyt production |
| `gen4-staging` | 364123201955 | eu-west-1 | core-platform-services | Gen4 staging |
| `gen4-production` | 470025225193 | eu-west-1 | core-platform-services | Gen4 production |
| `eu-central-1-pdv-prod-2` | 612833568613 | eu-central-1 | je-eksclusteradmin | EKS (JetConnect, eu-central-1) |
| `eu-west-1-plt-prod-1` | 459318535948 | eu-west-1 | je-eksclusteradmin | EKS (JetConnect, eu-west-1) |
| `eu-west-1-pdv-staging-1` | 280065845542 | eu-west-1 | core-platform-services | PDV staging (JetConnect) |
| `signature-deployer` | 772839078064 | eu-west-1 | core-platform-services | Signature deployer |
| `global-dns-non-production` | 409384221125 | eu-west-1 | je-read-write | Global DNS non-prod |
| `global-dns-production` | 202017898838 | eu-west-1 | je-read-write | Global DNS production |

## Disaster Recovery Accounts

On the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `p-ew1-drsecure` | 811869160850 | eu-west-1 | admin | DR secure |
| `p-ew1-drrecovery` | 414493223303 | eu-west-1 | admin | DR recovery |
| `p-ew1-dreks` | 536489505821 | eu-west-1 | admin | DR EKS |
| `p-ew1-drcommons` | 554674433462 | eu-west-1 | admin | DR commons |
| `p-ew1-drmarathon` | 709115367606 | eu-west-1 | admin | DR marathon |
| `d-ew1-test-dr-source` | 074795172184 | eu-west-1 | admin | DR test source |
| `d-ew1-test-dr-secure` | 239953716639 | eu-west-1 | admin | DR test secure |

## Infrastructure & GitLab Accounts

On the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `p-ew1-gitlab` | 176889707553 | eu-west-1 | admin | GitLab |
| `p-ew1-gitlabrunners` | 787947782836 | eu-west-1 | admin | GitLab runners |
| `infra-transit-staging-1` | 877320913035 | eu-west-1 | admin-view-only | Transit staging |
| `infra-transit-production-1` | 827332424127 | eu-west-1 | admin-view-only | Transit production |
| `vault-sops-568184606770` | 568184606770 | eu-west-1 | vault-sops | SOPS encryption (intsvc account) |

## Special / Other Accounts

On the **orga** portal.

| Profile | Account ID | Region | Role | Purpose |
|---------|-----------|--------|------|---------|
| `oomta` | 511343628249 | eu-west-1 | sdlc-oomta-admin | OOMTA |
| `hackathon_sandbox` | 404289934308 | eu-west-1 | hackathon-sandbox | Hackathon sandbox |
