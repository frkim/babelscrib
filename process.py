#  import libraries
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.document import DocumentTranslationClient

# create variables for your resource key, custom endpoint, sourceUrl, targetUrl, and targetLanguage
key = '25bn5qkT4iPMjJrO24alunq3o3arJaK8yogTqTtYzwokrLCrF59VJQQJ99BFAC5RqLJXJ3w3AAAbACOGjOic'
endpoint = 'https://babelscrib.cognitiveservices.azure.com'
sourceUri = 'https://babelscribdocs.blob.core.windows.net/source'
targetUri = 'https://babelscribdocs.blob.core.windows.net/target'
targetLanguage = 'en'


# initialize a new instance of the DocumentTranslationClient object to interact with the asynchronous Document translation feature
client = DocumentTranslationClient(endpoint, AzureKeyCredential(key))

# include source and target locations and target language code for the begin translation operation
poller = client.begin_translation(sourceUri, targetUri, targetLanguage)
result = poller.result()

print('Status: {}'.format(poller.status()))
print('Created on: {}'.format(poller.details.created_on))
print('Last updated on: {}'.format(poller.details.last_updated_on))
print(
    'Total number of translations on documents: {}'.format(
        poller.details.documents_total_count
    )
)

print('\nOf total documents...')
print('{} failed'.format(poller.details.documents_failed_count))
print('{} succeeded'.format(poller.details.documents_succeeded_count))

for document in result:
    print('Document ID: {}'.format(document.id))
    print('Document status: {}'.format(document.status))
    if document.status == 'Succeeded':
        print('Source document location: {}'.format(document.source_document_url))
        print(
            'Translated document location: {}'.format(document.translated_document_url)
        )
        print('Translated to language: {}\n'.format(document.translated_to))
    else:
        print(
            'Error Code: {}, Message: {}\n'.format(
                document.error.code, document.error.message
            )
        )