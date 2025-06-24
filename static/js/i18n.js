/**
 * BabelScrib i18n (Internationalization) Library
 * Simple client-side internationalization for BabelScrib
 */

// Translation dictionary
const translations = {    'en': {
        'document_upload': 'Document Upload',
        'go_to_homepage': 'Go to Homepage',
        'babelscrib_logo': 'BabelScrib Logo',
        'language': 'Language',
        'sign_out_account': 'Sign out of your account',
        'disconnect': 'Disconnect',
        'sign_in_account': 'Sign in to your account',
        'sign_in': 'Sign In',
        'test_azure_storage_configuration': 'Test Azure Storage Configuration',
        'storage_test': 'Storage Test',
        'document_translator': 'Document Translator',
        'click_here_to_select': 'Click here to select Documents button or drag and drop your files here',
        'supported_formats': 'Supported formats: pdf, docx, pptx, xlsx, txt, csv, md, etc.',
        'document_size_limit': 'Document size limit: ≤ 40MB per file • Up to 1000 files per batch • Total batch size ≤ 250MB',
        'view_azure_limits': 'View all Azure AI Translator limits',
        'select_documents': 'Select Documents',
        'your_email': 'Your email',
        'upload': 'Upload',
        'document_translation': 'Document Translation',        'translate_to': 'Translate to',
        'english': 'English',
        'spanish': 'Spanish', 
        'french': 'French',
        'german': 'German',
        'italian': 'Italian',
        'portuguese': 'Portuguese',
        'polish': 'Polish',
        'source_language': 'Source language',
        'auto_detect': 'Auto-detect',
        'cleanup_note': 'Note: Original uploaded files are automatically removed after translation is complete. Old translated documents (older than 24 hours) are automatically cleaned up when starting a new translation.',
        'translate_btn': 'Translate Documents',
        // File upload related
        'selected_files': 'Selected {count} file(s)',
        'click_add_documents': 'Click here to add other documents',
        'upload_complete': 'Upload Complete!',
        'successful_failed': 'Successful: {successful}, Failed: {failed}',
        'show_successful_uploads': 'Show successful uploads',        'file_uploaded_successfully': 'File uploaded successfully',        'uploading_files': 'Uploading {count} file(s)...',        'please_select_files_first': 'Please select files first.',
        'please_enter_valid_email': 'Please enter a valid email address',        'please_enter_email_address': 'Please enter your email address.',        'network_error_upload': 'Network error during upload.',        'upload_failed_generic': 'Upload failed.',
        'please_select_target_language': 'Please select a target language.',
        'translation_in_progress': 'Translation in Progress...',
        'translation_request_failed': 'Translation request failed. Please try again.',        'previous_files_cleared': 'Previous translation files were found and cleared automatically. Please try the translation again.',
        'launch_translation_process': 'Launch Translation Process',
        // Translation completion messages
        'translation_completed_successfully': 'Translation completed successfully!',
        'status_label': 'Status:',
        'total_documents': 'Total documents: {total}',
        'succeeded_label': 'Succeeded: {count}',
        'failed_label': 'Failed: {count}',        'automatically_removed_source_files': 'Automatically removed {count} source files.',
        'failed_cleanup_count': '({count} failed to clean)',        'failed_to_remove_source_files': 'Failed to automatically remove {count} source files.',
        'no_source_files_found': 'No source files found to remove.',
        'cleanup_not_performed': 'Automatic source cleanup was not performed: {reason}.',
        'view_translation_details': 'View translation details',
        'translated_to': 'Translated to: {language}',
        'download_translated_documents': 'Download Translated Documents:',        'download_translated_document': 'Download Translated Document',        'translation_failed': 'Failed',        'upload_failed': 'Upload failed: {error}',
        'translation_failed_error': 'Translation failed: {error}',
        // Translation process
        'starting_translation_process': 'Starting translation process',
        'preparing_documents': 'Starting translation process - Preparing documents for translation',
        'connecting_service': 'Starting translation process - Connecting to translation service',
        'processing_documents': 'Starting translation process - Processing documents',
        'translating_content': 'Starting translation process - Translating content',
        'finalizing_translation': 'Starting translation process - Finalizing translation',        'translation_process_seconds': 'Starting translation process ({seconds} seconds)',
        'connecting_service_seconds': 'Starting translation process - Connecting to translation service ({seconds} seconds)',
        'translating_content_seconds': 'Starting translation process - Translating content ({seconds} seconds)',
        'second': 'second',
        'seconds': 'seconds'
    },    'fr': {
        'document_upload': 'Téléchargement de Documents',
        'go_to_homepage': 'Aller à l\'Accueil',
        'babelscrib_logo': 'Logo BabelScrib',
        'language': 'Langue',
        'sign_out_account': 'Déconnectez-vous de votre compte',
        'disconnect': 'Déconnexion',
        'sign_in_account': 'Connectez-vous à votre compte',
        'sign_in': 'Se Connecter',
        'test_azure_storage_configuration': 'Tester la Configuration Azure Storage',
        'storage_test': 'Test de Stockage',
        'document_translator': 'Traducteur de Documents',
        'click_here_to_select': 'Cliquez ici pour sélectionner le bouton Documents ou déposez vos fichiers ici',
        'supported_formats': 'Formats supportés : pdf, docx, pptx, xlsx, txt, csv, md, etc.',
        'document_size_limit': 'Limite de taille : ≤ 40Mo par fichier • Jusqu\'à 1000 fichiers par lot • Taille totale ≤ 250Mo',
        'view_azure_limits': 'Voir toutes les limites d\'Azure AI Translator',
        'select_documents': 'Sélectionner des Documents',
        'your_email': 'Votre email',
        'upload': 'Télécharger',
        'document_translation': 'Traduction de Documents',        'translate_to': 'Traduire vers',
        'english': 'Anglais',
        'spanish': 'Espagnol',
        'french': 'Français',
        'german': 'Allemand',
        'italian': 'Italien',
        'portuguese': 'Portugais',
        'polish': 'Polonais',
        'source_language': 'Langue source',
        'auto_detect': 'Détection automatique',
        'cleanup_note': 'Note : Les fichiers téléchargés originaux sont automatiquement supprimés après la traduction. Les anciens documents traduits (de plus de 24 heures) sont automatiquement nettoyés lors du démarrage d\'une nouvelle traduction.',
        'translate_btn': 'Traduire les Documents',
        // File upload related
        'selected_files': '{count} fichier(s) sélectionné(s)',
        'click_add_documents': 'Cliquez ici pour ajouter d\'autres documents',
        'upload_complete': 'Téléchargement Terminé !',
        'successful_failed': 'Réussis : {successful}, Échoués : {failed}',
        'show_successful_uploads': 'Afficher les téléchargements réussis',        'file_uploaded_successfully': 'Fichier téléchargé avec succès',        'uploading_files': 'Téléchargement de {count} fichier(s)...',        'please_select_files_first': 'Veuillez d\'abord sélectionner des fichiers.',
        'please_enter_valid_email': 'Veuillez saisir une adresse email valide',        'please_enter_email_address': 'Veuillez saisir votre adresse email.',        'network_error_upload': 'Erreur réseau lors du téléchargement.',        'upload_failed_generic': 'Échec du téléchargement.',
        'please_select_target_language': 'Veuillez sélectionner une langue cible.',
        'translation_in_progress': 'Traduction en cours...',
        'translation_request_failed': 'Échec de la demande de traduction. Veuillez réessayer.',        'previous_files_cleared': 'Les fichiers de traduction précédents ont été trouvés et supprimés automatiquement. Veuillez relancer la traduction.',
        'launch_translation_process': 'Lancer le Processus de Traduction',
        // Translation completion messages
        'translation_completed_successfully': 'Traduction terminée avec succès !',
        'status_label': 'Statut :',
        'total_documents': 'Total de documents : {total}',
        'succeeded_label': 'Réussis : {count}',
        'failed_label': 'Échoués : {count}',        'automatically_removed_source_files': '{count} fichiers sources supprimés automatiquement.',
        'failed_cleanup_count': '({count} échecs de nettoyage)',        'failed_to_remove_source_files': 'Échec de la suppression automatique de {count} fichiers sources.',
        'no_source_files_found': 'Aucun fichier source trouvé à supprimer.',
        'cleanup_not_performed': 'Le nettoyage automatique des fichiers sources n\'a pas été effectué : {reason}.',
        'view_translation_details': 'Voir les détails de la traduction',
        'translated_to': 'Traduit vers : {language}',
        'download_translated_documents': 'Télécharger les Documents Traduits :',        'download_translated_document': 'Télécharger le Document Traduit',        'translation_failed': 'Échoué',        'upload_failed': 'Échec du téléchargement : {error}',
        'translation_failed_error': 'Échec de la traduction : {error}',
        // Translation process
        'starting_translation_process': 'Démarrage du processus de traduction',
        'preparing_documents': 'Démarrage du processus de traduction - Préparation des documents',
        'connecting_service': 'Démarrage du processus de traduction - Connexion au service de traduction',
        'processing_documents': 'Démarrage du processus de traduction - Traitement des documents',
        'translating_content': 'Démarrage du processus de traduction - Traduction du contenu',
        'finalizing_translation': 'Démarrage du processus de traduction - Finalisation de la traduction',        'translation_process_seconds': 'Démarrage du processus de traduction ({seconds} secondes)',
        'connecting_service_seconds': 'Démarrage du processus de traduction - Connexion au service de traduction ({seconds} secondes)',
        'translating_content_seconds': 'Démarrage du processus de traduction - Traduction du contenu ({seconds} secondes)',
        'second': 'seconde',
        'seconds': 'secondes'
    }
};

// Current language
let currentLanguage = 'en';

// Translation function with interpolation support
function t(key, params = {}) {
    let text = translations[currentLanguage][key] || translations['en'][key] || key;
    
    // Simple string interpolation
    if (typeof text === 'string' && Object.keys(params).length > 0) {
        Object.keys(params).forEach(paramKey => {
            text = text.replace(new RegExp(`{${paramKey}}`, 'g'), params[paramKey]);
        });
    }
    
    return text;
}

// Get user's preferred language from cookie or browser
function getPreferredLanguage() {
    // Check cookie first
    const cookieLang = getCookie('babelscrib_language');
    if (cookieLang && translations[cookieLang]) {
        return cookieLang;
    }
    
    // Check browser language
    const browserLang = navigator.language.split('-')[0];
    if (translations[browserLang]) {
        return browserLang;
    }
    
    // Default to French as specified in requirements
    return 'fr';
}

// Set language and update UI
function setLanguage(lang) {
    if (!translations[lang]) {
        console.warn(`Language ${lang} not supported, falling back to English`);
        lang = 'en';
    }
    
    currentLanguage = lang;
    setCookie('babelscrib_language', lang, 365);
    updateUI();
    
    // Update language selector
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.value = lang;
    }
    
    // Update HTML lang attribute
    document.documentElement.lang = lang;
}

// Update all translatable elements
function updateUI() {
    // Update title
    document.title = t('document_upload');
    
    // Update elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key);
        
        if (element.hasAttribute('data-i18n-attr')) {
            // Update attribute (e.g., title, alt, placeholder)
            const attr = element.getAttribute('data-i18n-attr');
            element.setAttribute(attr, translation);
        } else {
            // Update text content
            element.textContent = translation;
        }
    });
    
    // Update elements with data-i18n-html attribute (for HTML content)
    document.querySelectorAll('[data-i18n-html]').forEach(element => {
        const key = element.getAttribute('data-i18n-html');
        element.innerHTML = t(key);
    });
}

// Initialize i18n when DOM is loaded
function initI18n() {
    // Set initial language based on user preference
    const preferredLang = getPreferredLanguage();
    setLanguage(preferredLang);
    
    // Set up language selector change handler
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', function() {
            setLanguage(this.value);
        });
    }
}

// Cookie utility functions
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/; SameSite=Lax";
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length, c.length));
    } 
    return null;
}

// Export for use in global scope
window.BabelScribI18n = {
    t: t,
    setLanguage: setLanguage,
    currentLanguage: () => currentLanguage,
    initI18n: initI18n
};
