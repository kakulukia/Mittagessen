<template lang="pug">
.weekDay.special
  .date
    h4.orange-text Spezialität
    h4.orange-text der Woche
  .plans
    //div &nbsp;
    MealPlan(:plan="week.special_menu" @reload-week="$emit('reload-week')" v-if="week.special_menu")
    .mealPlan(v-if="!week.special_menu")
      v-combobox.left.nonVegi(
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
        tabindex="1"
      )
        template(v-slot:no-data)
          v-list-item
            v-list-item-content
              v-list-item-title Keine Übereinstimmung.
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
    props: ['week'],
    data () {
      return {
        newMeal: "",
        search: "",
        customToolbar: [
          ["bold", "italic", "image", { 'color': [] }],
          // [{ list: "ordered" }, { list: "bullet" }],
        ]
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
        this.axios.post('plans/', {meal_id: mealId})
            .then((response) => {
              let plan = response.data
              this.axios.put(`weeks/${this.week.id}/`, {special_menu_id: plan.id})
                .then(() => {
                  this.$emit('reload-week')
                  this.newMeal = undefined
                })
            })
      },
    }
  }
</script>

<style lang="sass">
.weekDay
  display: grid
  grid-template-columns: 120px 1fr
  margin-bottom: 1em
  &.special
    margin-bottom: 2em

@media screen and (max-width: 800px)
  .weekDay
    display: block
    .date
      display: flex
      h4
        margin-right: 5px


.mealPlan
  display: grid
  grid-template-columns: 1fr 85px 25px
  column-gap: 20px

.v-text-field
    margin-top: 0

.theme--light.v-text-field > .v-input__control > .v-input__slot:before
  border-color: #ddd

@media screen and (max-width: 400px)
  .mealPlan
    grid-template-columns: 1fr 60px 25px
    column-gap: 10px

.green-text
  color: green

.altText
  width: calc(100% - 153px)

.closed
  cursor: pointer
  margin-top: 5px
  color: #ccc
  &:hover
    color: #000

.orange-text
  color: #ED7A18
</style>
