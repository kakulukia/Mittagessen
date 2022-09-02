import Vue from 'vue';
import de from 'vuetify/lib/locale/de';
import Vuetify, { VSnackbar, VBtn, VIcon } from 'vuetify/lib'
import VuetifyToast from 'vuetify-toast-snackbar'

Vue.use(Vuetify, {
  components: {
    VSnackbar,
    VBtn,
    VIcon
  }
})
Vue.use(VuetifyToast, {
  x: 'right', // default
  y: 'top', // default
  color: 'info', // default
  iconColor: '', // default
  timeout: 3000, // default
  dismissable: true, // default
  multiLine: false, // default
  vertical: false, // default
  queueable: false, // default
  showClose: false, // default
  closeText: '', // default
  closeIcon: 'close', // default
  closeColor: '', // default
  slot: [], //default
  shorts: {
    custom: {
      color: 'purple'
    }
  },
  property: '$toast' // default
})

export default new Vuetify({
  icons: {
    iconfont: 'mdi', // default - only for display purposes
  },
  theme: {
    dark: false,
    options: {
      customProperties: true,
    },
    themes: {
      light: {
        primary: '#0DB3DD',
        secondary: '#424242',
        accent: '#1B2530',
        error: '#FF5252',
        info: '#2196F3',
        success: '#4CAF50',
        warning: '#FFC107'
      },
    },
  },
  lang: {
    locales: { de },
    current: 'de',
  },
});
