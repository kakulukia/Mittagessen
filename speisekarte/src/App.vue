<template lang="pug">
v-app
  //v-navigation-drawer#nav(permanent app color="accent" dark mini-variant v-if="user")
    v-list-item.px-2
      v-list-item-avatar {{ user.avatar_name }}

    v-list(dense nav)
      v-list-item(v-if="user")
        a(:href="this.$root.apiHost + '/monitor/logout/'" title="Logout")
          v-icon mdi-logout
    v-divider.menu

    v-list(dense nav)
      template(v-for="item in menuItems")
        template(v-if="hasPermissions(item.permissions)")
          v-list-item(v-if="oldAdminLink(item.to)" :href="item.to" :target="item.target" :title="item.title")
            v-list-item-icon
              v-icon {{ item.icon }}

            v-list-item-content
              v-list-item-title {{ item.title }}
          v-list-item(v-else :to="{name: item.to}" :title="item.title")
            v-list-item-icon
              v-icon {{ item.icon }}

            v-list-item-content
              v-list-item-title {{ item.title }}
    #caution.caution(:class="{'testing': testEnvironment}")

  v-main(v-if="user")
    router-view
</template>

<script>

import {useStore} from '@/store'
import {storeToRefs} from 'pinia'

export default {
  name: 'App',
  setup(){
    const store = useStore()
    const { meals } = storeToRefs(store)
    store.loadItems()
    return {
      meals,
    }
  },
  data: () => ({
    user: undefined,
    menuItems: [],
  }),
  created (){
    this.axios.get('current-user/')
      .then((response) => {
          this.user = response.data
      }).catch((error) => {
        if (error.response.status === 401) {
          window.location.href = this.$root.apiHost + '/admin/login/'
        }
      });
  },
  computed: {
  },
  methods: {
  }
};
</script>

<style lang="sass">
</style>
