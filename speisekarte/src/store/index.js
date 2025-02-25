import { defineStore } from 'pinia'

export const useStore = defineStore('main', {
  state: () => {
		return {
			meals: [],
		}
	},
  // could also be defined as
  // state: () => ({ count: 0 })
  actions: {
    loadItems() {
      this.api.get('meals')
        .then((response) => {
          this.meals = response.data
      })
    },
    loadCustomers() {
      this.api.get('customers')
        .then((response) => {
          this.customers = response.data
      })
    }
  },
})
