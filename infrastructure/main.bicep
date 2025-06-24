// Target scope for resource group deployment
targetScope = 'resourceGroup'

// Parameters with descriptions and validation
@description('Azure region for resource deployment')
param location string = 'westeurope'

@description('Global location for DNS services')
param globalLocation string = 'global'

@description('Environment name for resource naming')
@allowed(['dev', 'staging', 'prod'])
param environmentName string = 'prod'

@description('Unique suffix for resource naming to ensure global uniqueness')
param resourceToken string = uniqueString(resourceGroup().id)

@description('Microsoft OAuth client ID for authentication')
@secure()
param microsoftClientId string

@description('Microsoft OAuth client secret for authentication')
@secure()
param microsoftClientSecret string

@description('Domain name for the application')
param domainName string = 'babelscrib.com'

@description('Log Analytics retention period in days')
@minValue(30)
@maxValue(730)
param logRetentionDays int = 30

@description('Production minimum replicas')
@minValue(1)
param prodMinReplicas int = 1

@description('Production maximum replicas')
@minValue(1)
param prodMaxReplicas int = 3

@description('Development minimum replicas')
@minValue(0)
param devMinReplicas int = 0

@description('Development maximum replicas')
@minValue(1)
param devMaxReplicas int = 2

@description('Production CPU allocation')
param cpuProd string = '0.5'

@description('Production memory allocation')
param memoryProd string = '1Gi'

@description('Development CPU allocation')
param cpuDev string = '0.25'

@description('Development memory allocation')
param memoryDev string = '0.5Gi'

// Variables for consistent resource naming
var resourceNames = {
  containerRegistry: 'cr${resourceToken}'
  storageAccount: 'st${resourceToken}'
  logAnalytics: 'log-${resourceToken}'
  containerAppEnv: 'cae-${resourceToken}'
  containerApp: 'ca-babelscrib-${environmentName}-${resourceToken}'
  containerAppDev: 'ca-babelscrib-dev-${resourceToken}'
  translator: 'cog-translator-${resourceToken}'
  userAssignedIdentity: 'id-${resourceToken}'
}

// Common tags
var commonTags = {
  environment: environmentName
  project: 'babelscrib'
  'azd-env-name': resourceToken
}

// User-assigned managed identity for secure resource access
resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: resourceNames.userAssignedIdentity
  location: location
  tags: commonTags
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-10-01' = {
  name: resourceNames.logAnalytics
  location: location
  tags: commonTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: logRetentionDays
    workspaceCapping: {
      dailyQuotaGb: 1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: resourceNames.containerAppEnv
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

// Managed Certificate for Custom Domain
resource managedCertificate 'Microsoft.App/managedEnvironments/managedCertificates@2023-05-01' = {
  name: 'babelscrib-certificate'
  parent: containerAppEnv
  location: location
  properties: {
    subjectName: domainName
    domainControlValidation: 'CNAME'
  }
}

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: resourceNames.containerRegistry
  location: location
  tags: commonTags
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
    anonymousPullEnabled: false
    dataEndpointEnabled: false
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Role assignment for user-assigned identity to pull from ACR
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, userAssignedIdentity.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage Account
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: resourceNames.storageAccount
  location: location
  tags: commonTags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Role assignment for user-assigned identity to access storage
resource storageDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, userAssignedIdentity.id, 'storageblobdatacontributor')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Translator (Cognitive Services)
resource translator 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: resourceNames.translator
  location: location
  tags: commonTags
  kind: 'TextTranslation'
  sku: {
    name: 'S1'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    apiProperties: {}
    networkAcls: {
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

// Role assignment for user-assigned identity to access Translator
resource translatorUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(translator.id, userAssignedIdentity.id, 'cognitiveservicesuser')
  scope: translator
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908') // Cognitive Services User
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// DNS Zone (optional - remove if not needed)
resource dnsZone 'Microsoft.Network/dnsZones@2023-07-01' = if (environmentName == 'prod') {
  name: domainName
  location: globalLocation
  tags: commonTags
}

// App Service Domain (optional - remove if not needed)
resource appServiceDomain 'Microsoft.DomainRegistration/domains@2023-01-01' = if (environmentName == 'prod') {
  name: domainName
  location: globalLocation
  tags: commonTags
  properties: {
    contactAdmin: {
      name: 'Admin Contact'
      email: 'admin@${domainName}'
      addressMailing: {
        address1: '123 Main St'
        city: 'Amsterdam'
        country: 'NL'
        postalCode: '1000AA'
        state: 'NH'
      }
      phone: '+31.123456789'
    }
    contactBilling: {
      name: 'Billing Contact'
      email: 'billing@${domainName}'
      addressMailing: {
        address1: '123 Main St'
        city: 'Amsterdam'
        country: 'NL'
        postalCode: '1000AA'
        state: 'NH'
      }
      phone: '+31.123456789'
    }
    contactRegistrant: {
      name: 'Registrant Contact'
      email: 'registrant@${domainName}'
      addressMailing: {
        address1: '123 Main St'
        city: 'Amsterdam'
        country: 'NL'
        postalCode: '1000AA'
        state: 'NH'
      }
      phone: '+31.123456789'
    }
    contactTech: {
      name: 'Tech Contact'
      email: 'tech@${domainName}'
      addressMailing: {
        address1: '123 Main St'
        city: 'Amsterdam'
        country: 'NL'
        postalCode: '1000AA'
        state: 'NH'
      }
      phone: '+31.123456789'
    }
    autoRenew: true
    privacy: true
    dnsType: 'AzureDns'
  }
}

// Container App: Production
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: resourceNames.containerApp
  location: location
  tags: union(commonTags, { 'azd-service-name': 'babelscrib' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  properties: {
    environmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: acr.properties.loginServer
          identity: userAssignedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'microsoft-client-secret'
          value: microsoftClientSecret
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'babelscrib'
          image: '${acr.properties.loginServer}/babelscrib:prod'
          resources: {
            cpu: json(cpuProd)
            memory: memoryProd
          }
          env: [
            {
              name: 'DJANGO_SETTINGS_MODULE'
              value: 'api.settings'
            }
            {
              name: 'MICROSOFT_CLIENT_ID'
              value: microsoftClientId
            }
            {
              name: 'MICROSOFT_CLIENT_SECRET'
              secretRef: 'microsoft-client-secret'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              value: storage.name
            }
            {
              name: 'AZURE_TRANSLATOR_ENDPOINT'
              value: translator.properties.endpoint
            }
            {
              name: 'AZURE_TRANSLATOR_REGION'
              value: location
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: userAssignedIdentity.properties.clientId
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health/'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/ready/'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 15
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: prodMinReplicas
        maxReplicas: prodMaxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
    ingress: {
      external: true
      targetPort: 8000
      transport: 'auto'
      allowInsecure: false
      corsPolicy: {
        allowedOrigins: ['*']
        allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        allowedHeaders: ['*']
        allowCredentials: true
      }
      customDomains: environmentName == 'prod' ? [
        {
          name: 'www.${domainName}'
          bindingType: 'SniEnabled'
          certificateId: managedCertificate.id
        }
        {
          name: domainName
          bindingType: 'SniEnabled'
          certificateId: managedCertificate.id
        }
      ] : []
    }
  }
  dependsOn: [
    acrPullRoleAssignment
    storageDataContributorRoleAssignment
    translatorUserRoleAssignment
  ]
}

// Container App: Development
resource containerAppDev 'Microsoft.App/containerApps@2024-03-01' = if (environmentName != 'prod') {
  name: resourceNames.containerAppDev
  location: location
  tags: union(commonTags, { 'azd-service-name': 'babelscrib-dev' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  properties: {
    environmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: acr.properties.loginServer
          identity: userAssignedIdentity.id
        }
      ]
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'babelscrib-dev'
          image: '${acr.properties.loginServer}/babelscrib:latest'
          resources: {
            cpu: json(cpuDev)
            memory: memoryDev
          }
          env: [
            {
              name: 'DJANGO_SETTINGS_MODULE'
              value: 'api.settings'
            }
            {
              name: 'DEBUG'
              value: 'True'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              value: storage.name
            }
            {
              name: 'AZURE_TRANSLATOR_ENDPOINT'
              value: translator.properties.endpoint
            }
            {
              name: 'AZURE_TRANSLATOR_REGION'
              value: location
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: userAssignedIdentity.properties.clientId
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health/'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/ready/'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 15
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: devMinReplicas
        maxReplicas: devMaxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
    ingress: {
      external: true
      targetPort: 8000
      transport: 'auto'
      allowInsecure: false
      corsPolicy: {
        allowedOrigins: ['*']
        allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        allowedHeaders: ['*']
        allowCredentials: true
      }
    }
  }
  dependsOn: [
    acrPullRoleAssignment
    storageDataContributorRoleAssignment
    translatorUserRoleAssignment
  ]
}

// Outputs
@description('User-assigned managed identity ID')
output userAssignedIdentityId string = userAssignedIdentity.id

@description('User-assigned managed identity client ID')
output userAssignedIdentityClientId string = userAssignedIdentity.properties.clientId

@description('Container App name')
output containerAppName string = containerApp.name

@description('Container App FQDN')
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Container App Dev name')
output containerAppDevName string = environmentName != 'prod' ? containerAppDev.name : ''

@description('Container App Dev FQDN')
output containerAppDevFqdn string = environmentName != 'prod' ? containerAppDev.properties.configuration.ingress.fqdn : ''

@description('Azure Container Registry login server')
output acrLoginServer string = acr.properties.loginServer

@description('Storage account name')
output storageAccountName string = storage.name

@description('Storage account primary endpoint')
output storageAccountPrimaryEndpoint string = storage.properties.primaryEndpoints.blob

@description('Translator endpoint')
output translatorEndpoint string = translator.properties.endpoint

@description('Translator region')
output translatorRegion string = translator.location

@description('DNS Zone ID')
output dnsZoneId string = environmentName == 'prod' ? dnsZone.id : ''

@description('App Service Domain ID')
output appServiceDomainId string = environmentName == 'prod' ? appServiceDomain.id : ''

@description('Log Analytics workspace ID')
output logAnalyticsWorkspaceId string = logAnalytics.id

@description('Resource group name')
output resourceGroupName string = resourceGroup().name

@description('Container Apps Environment ID')
output containerAppEnvironmentId string = containerAppEnv.id
