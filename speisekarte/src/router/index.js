import Vue from 'vue';
import Router from 'vue-router';
import KuecheView from '@/views/KuecheView.vue'; // Deine Küche-Komponente
import AbrechnungenView from '@/views/AbrechnungenView.vue'; // Neue Abrechnungen-Komponente

Vue.use(Router);

export default new Router({
  mode: 'history', // Aktiviert saubere URLs
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/kueche',
      name: 'Kueche',
      component: KuecheView,
    },
    {
      path: '/abrechnungen',
      name: 'Abrechnungen',
      component: AbrechnungenView,
    },
    {
      path: '/',
      redirect: '/kueche', // Startseite als Redirect zu Küche
    },
  ],
});
