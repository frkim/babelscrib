param location string = 'westeurope'
param globalLocation string = 'global'
param containerRegistryName string = 'babelscrib'
param storageAccountName string = 'babelscribdocs'
param logAnalyticsName string = 'babelscribacala'
param containerAppEnvName string = 'babelscribacaenv'
param containerAppName string = 'babelscrib'
param containerAppDevName string = 'babelscrib-dev'
param translatorName string = 'babelscrib-translator'
param dnsZoneName string = 'babelscrib.com'
param appServiceDomainName string = 'babelscrib.com'
param logRetentionDays int = 30
param prodMinReplicas int = 1
param prodMaxReplicas int = 3
param devMinReplicas int = 1
param devMaxReplicas int = 2
param cpuProd number = 0.5
param memoryProd string = '1Gi'
param cpuDev number = 0.5
param memoryDev string = '1Gi'
param tags object = {
  environment: 'production'
  project: 'babelscrib'
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  sku: {
    name: 'PerGB2018'
  }
  properties: {
    retentionInDays: logRetentionDays
  }
}

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys('2023-10-01').primarySharedKey
      }
    }
  }
}

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Storage Account
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
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
  }
}

// Translator (Cognitive Services)
resource translator 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: translatorName
  location: location
  tags: tags
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
  }
}

// DNS Zone
resource dnsZone 'Microsoft.Network/dnsZones@2023-07-01' = {
  name: dnsZoneName
  location: globalLocation
  tags: tags
}

// App Service Domain
resource appServiceDomain 'Microsoft.DomainRegistration/domains@2023-01-01' = {
  name: appServiceDomainName
  location: globalLocation
  tags: tags
  properties: {
    contactAdmin: {
      name: 'Admin Contact'
      email: 'admin@babelscrib.com'
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
      email: 'billing@babelscrib.com'
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
      email: 'registrant@babelscrib.com'
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
      email: 'tech@babelscrib.com'
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
  name: containerAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppEnv.id
    configuration: {
      registries: [
        {
          server: '${acr.name}.azurecr.io'
        }
      ]
      secrets: [
        {
          name: 'microsoft-client-secret'
          value: 'your-microsoft-client-secret-here'  // Replace with actual secret or parameter
        }
      ]
      activeRevisionsMode: 'Single'
    }
    template: {
      containers: [        {
          name: containerAppName
          image: '${acr.name}.azurecr.io/${containerAppName}:prod'
          resources: {
            cpu: cpuProd
            memory: memoryProd
          }
          env: [
            {
              name: 'DJANGO_SETTINGS_MODULE'
              value: 'api.settings'
            }
            {
              name: 'MICROSOFT_CLIENT_ID'
              value: 'fcfbaf73-654e-49a7-9141-b994192888c6'
            }
            {
              name: 'MICROSOFT_CLIENT_SECRET'
              secretRef: 'microsoft-client-secret'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/ready'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 15
            }
          ]
        }
      ]
      scale: {
        minReplicas: prodMinReplicas
        maxReplicas: prodMaxReplicas
      }
    }
    ingress: {      external: true
      targetPort: 8000
      transport: 'auto'
      allowInsecure: false
    }
  }
}

// Container App: Dev
resource containerAppDev 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppDevName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppEnv.id
    configuration: {
      registries: [
        {
          server: '${acr.name}.azurecr.io'
        }
      ]
      secrets: []
      activeRevisionsMode: 'Single'
    }
    template: {
      containers: [
        {
          name: containerAppDevName
          image: '${acr.name}.azurecr.io/${containerAppDevName}:latest'
          resources: {
            cpu: cpuDev
            memory: memoryDev
          }
          env: [
            {
              name: 'DJANGO_SETTINGS_MODULE'
              value: 'api.settings'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/ready'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 15
            }
          ]
        }
      ]
      scale: {
        minReplicas: devMinReplicas
        maxReplicas: devMaxReplicas
      }
    }
    ingress: {
      external: true
      targetPort: 8000
      transport: 'auto'
      allowInsecure: false
    }
  }
}

// Outputs
output containerAppName string = containerApp.name
output containerAppDevName string = containerAppDev.name
output acrLoginServer string = acr.properties.loginServer
output storageAccountName string = storage.name
output translatorEndpoint string = translator.properties.endpoint
output dnsZoneId string = dnsZone.id
output appServiceDomainId string = appServiceDomain.id
output logAnalyticsWorkspaceId string = logAnalytics.id
