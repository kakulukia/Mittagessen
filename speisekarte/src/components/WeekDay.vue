<template lang="pug">
  .weekDay
    h2 {{ day.dateDisplay }}
    MealPlan(v-for="plan in day.plans" :plan="plan" :key="plan.id" @reload-week="$emit('reload-week')")
    .mealPlan
      v-combobox.left(
        ref="newEntry"
        auto-select-first
        v-model="newMeal"
        :items="meals"
        item-text="name"
        item-value="id"
        @keydown.stop.prevent.enter="handleEnter($event, day.id)"
        :search-input.sync="search"
        dense
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
      handleEnter(event, dayId) {
        event.preventDefault()
        let searchText = this.search ? this.search.trim() : '';
        const box = this.$refs.newEntry
        let itemFound = box.filteredItems.length;
        console.log(itemFound)
        if (!itemFound && searchText.length) {
          this.axios.post('meals/', {name: searchText})
              .then((response) => {
                this.store.loadItems()
                this.addPlan(response.data.id, dayId)
                box.isMenuActive = false
                this.search = ""
              })
        }
        if (itemFound) {
          setTimeout(() => {
            this.addPlan(this.newMeal.id, dayId)
            this.newMeal = undefined
          },100)
        }
      },
      addPlan(mealId, dayId) {
        this.axios.post('plans/', {day: dayId, meal_id: mealId})
            .then(() => {
              this.$emit('reload-week')
              this.newMeal = undefined
            })
      }
    }
  }
</script>

<style lang="sass">
.left
  margin-left: 200px
</style>
