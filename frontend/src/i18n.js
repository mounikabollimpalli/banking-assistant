export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'te', label: 'తెలుగు' },
]

const STRINGS = {
  en: {
    dashboard: 'Dashboard', transactions: 'Transactions', transfer: 'Move Money',
    admin: 'Compliance (Admin)', logout: 'Log out', balance: 'Total balance',
    recent: 'Recent transactions', assistant: 'Banking Assistant',
    askPlaceholder: 'Ask about your balance, spending...',
  },
  hi: {
    dashboard: 'डैशबोर्ड', transactions: 'लेन-देन', transfer: 'पैसे भेजें',
    admin: 'अनुपालन (एडमिन)', logout: 'लॉग आउट', balance: 'कुल शेष',
    recent: 'हाल के लेन-देन', assistant: 'बैंकिंग सहायक',
    askPlaceholder: 'अपने बैलेंस, खर्च के बारे में पूछें...',
  },
  te: {
    dashboard: 'డాష్‌బోర్డ్', transactions: 'లావాదేవీలు', transfer: 'డబ్బు పంపండి',
    admin: 'కంప్లయన్స్ (అడ్మిన్)', logout: 'లాగ్ అవుట్', balance: 'మొత్తం బ్యాలెన్స్',
    recent: 'ఇటీవలి లావాదేవీలు', assistant: 'బ్యాంకింగ్ సహాయకుడు',
    askPlaceholder: 'మీ బ్యాలెన్స్, ఖర్చుల గురించి అడగండి...',
  },
}

export function t(lang, key) {
  return (STRINGS[lang] && STRINGS[lang][key]) || STRINGS.en[key] || key
}
