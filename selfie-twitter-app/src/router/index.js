import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import DefaultLayout from '../layouts/Default.vue'

Vue.use(VueRouter)

const router = new VueRouter({
  routes: [
    {
      path: "/",
      component: DefaultLayout,
      children: [
        {
          path: "",
          name: "home",
          component: Home,
          alias: "/home",
        },
        {
          path: '/stats', 
          name: 'stats', 
          component: () => import(/* webpackChunkName: "about" */ '../views/Stats.vue')
        }
      ]
    }
  ]
});

export default router
