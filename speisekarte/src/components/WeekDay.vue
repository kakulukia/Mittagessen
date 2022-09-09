<template lang="pug">
  .weekDay
    h2 {{ day.dateDisplay }}
    MealPlan(v-for="plan in day.plans" :plan="plan" :key="plan.id")
    v-combobox(
      auto-select-first
      v-model="newMeal"
      :items="meals"
      item-text="name"
      item-value="id"
      @keydown.enter="handleEnter($event)"
      :search-input.sync="search"
    )
      template(v-slot:no-data)
        v-list-item
          v-list-item-content
            v-list-item-title Keine Übereinstimmung für "<strong>{{ search }}</strong>".
              |  <kbd>Enter</kbd> speichert das neue Gericht.

</template>

<script>
  import MealPlan from '@/components/MealPlan'
  import { storeToRefs } from 'pinia'
  import { useStore } from '@/store'

  export default {
    name: 'WeekDay',
    setup(){
      const store = useStore()
      const { meals } = storeToRefs(store)
      return {
        meals, store
      }
    },
    components: {MealPlan},
    props: ['day'],
    data () {
      return {
        newMeal: "",
        search: "",
      }
    },
    created () {
    },
    methods: {
      handleEnter(event) {
        event.preventDefault()
        if (!this.newMeal) {
          this.axios.post('meals/', {name: this.search}).then(() => this.store.loadItems())
        }
      }
    }
  }
</script>
