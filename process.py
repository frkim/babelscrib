# Import the translation service library
from lib.translation_service import create_translation_service, translate_documents_simple
from lib.config import get_config
import json


def main():
    """Main function to demonstrate the translation service usage."""
    
    # Get configuration
    config = get_config()
    
    # You can override default values from config if needed
    source_uri = config.source_uri
    target_uri = config.target_uri
    target_language = 'en'
    
    try:
        # Method 1: Using the simple convenience function
        print("Starting document translation using simple method...")
        result = translate_documents_simple(
            source_uri=source_uri,
            target_uri=target_uri,
            target_language=target_language
        )
        
        # Alternative Method 2: Using the service class directly
        # translation_service = create_translation_service()
        # result = translation_service.translate_documents(
        #     source_uri=source_uri,
        #     target_uri=target_uri,
        #     target_language=target_language
        # )
        
        # Display results
        print('Status: {}'.format(result['status']))
        print('Created on: {}'.format(result['created_on']))
        print('Last updated on: {}'.format(result['last_updated_on']))
        print('Total number of translations on documents: {}'.format(result['total_documents']))
        
        print('\nOf total documents...')
        print('{} failed'.format(result['failed_documents']))
        print('{} succeeded'.format(result['succeeded_documents']))
        
        # Display individual document results
        for document in result['documents']:
            print('Document ID: {}'.format(document['id']))
            print('Document status: {}'.format(document['status']))
            if document['status'] == 'Succeeded':
                print('Source document location: {}'.format(document['source_document_url']))
                print('Translated document location: {}'.format(document['translated_document_url']))
                print('Translated to language: {}\n'.format(document['translated_to']))
            else:
                if document['error']:
                    print('Error Code: {}, Message: {}\n'.format(
                        document['error']['code'], 
                        document['error']['message']
                    ))
        
        # Optionally save results to JSON file
        with open('translation_results.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print('\nResults saved to translation_results.json')
        
    except Exception as e:
        print(f'Translation failed: {str(e)}')


if __name__ == '__main__':
    main()