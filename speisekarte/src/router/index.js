import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
// import WorkingHours from '../views/WorkingHours.vue'
// import WorkingHoursIndex from '../views/WorkingHoursIndex.vue'
// import WorkingHoursDetail from '../views/WorkingHoursDetail.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  }
  // {
  //   path: '/Anwesenheiten/',
  //   // route level code-splitting
  //   // this generates a separate chunk (about.[hash].js) for this route
  //   // which is lazy-loaded when the route is visited.
  //   component: WorkingHoursIndex,
  //   children: [
  //     {
  //       path: '',
  //       name: 'Anwesenheiten',
  //       component: WorkingHours,
  //       props: true
  //     },
  //     {
  //       path: ':id',
  //       name: 'WorkingDetail',
  //       component: WorkingHoursDetail,
  //       props: true
  //     }
  //   ]
  // },
]

const router = new VueRouter({
  mode: 'history',
  base: '/admin/',
  routes
})

export default router
