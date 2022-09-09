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
        @keydown.stop.prevent.enter="handleEnter($event)"
        :search-input.sync="search"
        dense
        hide-details="auto"
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
        let searchText = this.search ? this.search.trim() : '';
        const box = this.$refs.newEntry
        let itemFound = box.filteredItems.length;
        console.log(itemFound)
        if (!itemFound && searchText.length) {
          this.axios.post('meals/', {name: searchText})
              .then((response) => {
                this.store.loadItems()
                this.addPlan(response.data.id)
                box.isMenuActive = false
                this.search = ""
              })
        }
        if (itemFound) {
          setTimeout(() => {
            this.addPlan(this.newMeal.id)
            this.newMeal = undefined
          },100)
        }
      },
      addPlan(mealId) {
        this.axios.post('plans/', {day: this.day.id, meal_id: mealId})
            .then(() => {
              this.$emit('reload-week')
              this.newMeal = undefined
            })
      }
    }
  }
</script>

<style lang="sass">
.mealPlan
  display: grid
  grid-template-columns: 1fr 80px 50px
  column-gap: 20px

.v-text-field
    margin-top: 0

@media screen and (min-width: 400px)
  .left
    margin-left: 200px

@media screen and (max-width: 400px)
  .mealPlan
    grid-template-columns: 1fr 60px 25px
    column-gap: 10px
</style>
