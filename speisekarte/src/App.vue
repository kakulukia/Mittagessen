<template lang="pug">
v-app
  v-main(v-if="user")
    router-view
</template>

<script>

import {useStore} from '@/store'
import {storeToRefs} from 'pinia'

export default {
  name: 'App',
  inject: ['apiHost'],
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
          window.location.href = this.apiHost + '/admin/login/?next=/kueche/'
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
html, body
  height: 100svh
  overflow: hidden
#app
  height: 100svh
  overflow-y: scroll
h1
  font-size: 18px

#app
  overflow-y: scroll

body .v-application a
  color: purple
  text-decoration: none
</style>
