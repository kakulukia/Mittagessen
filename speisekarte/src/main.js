import Vue from 'vue'
import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import { useStore } from './store'
import vuetify from './plugins/vuetify'
import 'roboto-fontface/css/roboto/roboto-fontface.css'
import { createPinia, PiniaVuePlugin } from 'pinia'
import Vue2Editor from "vue2-editor";

import axios from 'axios'
import VueAxios from 'vue-axios'
import { wrapper } from 'axios-cookiejar-support'
import { CookieJar } from 'tough-cookie'


Vue.config.productionTip = false

const jar = new CookieJar();

let apiUrl = window.location.protocol + '//' + window.location.hostname
if (window.location.hostname === 'localhost' || window.location.hostname.startsWith('192.')) {
  apiUrl += ':8000'
}
let apiHost = apiUrl
apiUrl += '/api'

console.log(apiUrl)

const client = wrapper(axios.create({
    baseURL: apiUrl,
    jar,
    withCredentials: true
}));

Vue.use(VueAxios, client)
const moment = require('moment')
require('moment/locale/de')
Vue.use(require('vue-moment'), {moment})

Vue.use(PiniaVuePlugin)
function AxiosPiniaPlugin() {
  return { api: client }
}
const pinia = createPinia()
pinia.use(AxiosPiniaPlugin)
Vue.use(Vue2Editor);


Vue.filter('de', function (value) {
  if (!value) return '0'
  return value.toLocaleString('de', {minimumFractionDigits: 2, maximumFractionDigits: 2})
})
Vue.filter('de0', function (value) {
  if (!value) return '0'
  return value.toLocaleString('de', {minimumFractionDigits: 0, maximumFractionDigits: 0})
})

const app = new Vue({
  router,
  useStore,
  vuetify,
  data: {
    apiHost
  },
  pinia,
  render: h => h(App)
})

if (!Date.prototype.toISODate) {
  Date.prototype.toISODate = function() {
    return this.getFullYear() + '-' +
      ('0' + (this.getMonth() + 1)).slice(-2) + '-' +
      ('0' + this.getDate()).slice(-2);
  }
}
Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}

app.$mount('#app')
