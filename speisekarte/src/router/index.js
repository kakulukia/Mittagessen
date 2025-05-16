import Vue from 'vue';
import Router from 'vue-router';
import KuecheView from '@/views/KuecheView.vue'; // Deine Küche-Komponente
import AbrechnungenView from '@/views/AbrechnungenView.vue'; // Neue Abrechnungen-Komponente
import LieferungenView from '@/views/LieferungenView.vue'; // Neue Lieferungen-Komponente
import RechnungenView from '@/views/RechnungenView.vue'; // Neue Rechnungen-Komponente
import RechnungEditView from '@/views/RechnungEditView.vue';

Vue.use(Router);

export default new Router({
  mode: 'history', // Aktiviert saubere URLs
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'Kueche',
      component: KuecheView,
    },
    {
      path: '/abrechnungen',
      name: 'Abrechnungen',
      component: AbrechnungenView,
    },
    {
      path: '/lieferungen',
      name: 'Lieferungen',
      component: LieferungenView,
    },
    {
      path: '/rechnungen',
      name: 'Rechnungen',
      component: RechnungenView,
    },
    {
      path: '/abrechnungen/:id',
      name: 'RechnungEdit',
      component: RechnungEditView,
    }
  ],
});
