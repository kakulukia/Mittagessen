<template lang="pug">
.mealPlan
  .combobox
    v-combobox.left(
      ref="newEntry"
      auto-select-first
      v-model="plan.meal"
      :items="meals"
      item-text="name"
      item-value="id"
      dense
      @change="updatePlan()"
      hide-details="auto"
      tabindex="1"
      @keydown.stop.prevent.enter="handleEnter($event)"
      @keydown.tab="handleTab"
      :search-input.sync="search"
      :class="{vegi: plan.meal.vegi, nonVegi: !plan.meal.vegi, bold: plan.meal.headline}"
    )
      //template(slot="selection" slot-scope="data")
        div(:class="{vegi: data.item.vegi}") {{ data.item.name }}
      template(v-slot:no-data)
        v-list-item
          v-list-item-content
            v-list-item-title Keine Übereinstimmung.
              |  <kbd>Enter</kbd> speichert das neue Gericht.
    v-btn(icon x-small)
      v-icon(
        x-small @click="switchHeadline()"
        :color="plan.meal.headline ? 'black' : 'grey lighten-1'") mdi-ab-testing
    v-btn(icon x-small)
      v-icon(
        small @click="switchVegi()"
        :color="(plan.meal && plan.meal.vegi) ? 'success darken-2' : 'grey lighten-1'") mdi-leaf
    //v-btn(icon x-small)
      v-icon(
        small @click="switchVegan()"
        :color="plan.meal.vegan ? 'yellow darken-2' : 'grey lighten-1'") mdi-barley

  v-text-field.right(v-if="!plan.meal.headline"
    v-model="plan.price"
    hide-details
    single-line
    type="number"
    dense
    @change="updatePlan()"
    @focus="$event.target.select()"
    tabindex="2"
  )
    v-icon(slot="append") mdi-currency-eur
  span(v-if="plan.meal.headline" )

  v-btn.delete(icon x-small color="red darken-4" @click="deleteMe()" tabindex="-1")
    v-icon mdi-delete-outline
</template>

<script>
  import {useStore} from '@/store'
  import {storeToRefs} from 'pinia'

  export default {
    name: 'MealPlan',
    props: ['plan'],
    setup(){
      const store = useStore()
      const { meals } = storeToRefs(store)
      return {
        meals, store
      }
    },
    data () {
      return {
        search: "huhu"
      }
    },
    created () {

    },
    methods: {
      handleTab() {
        // Hole das Vuetify-Combobox-Element
        const combobox = this.$refs.newEntry;

        // Prüfe, ob das Dropdown-Menü geöffnet ist und ein Element hervorgehoben ist
        if (combobox.isMenuActive && combobox.filteredItems.length > 0) {
          // Wähle das aktuell hervorgehobene Element aus
          const highlightedIndex = combobox.getMenuIndex()
          if (highlightedIndex !== -1) {
            const meal = combobox.filteredItems[highlightedIndex]
            const plan = this.plan
            plan.meal_id = meal.id
            plan.meal = meal
            this.axios.put('plans/' + plan.id + '/', plan)
              .then(() => {this.$emit('reload-week')})
          }
        }
      },
      nameDisplay(data) {
        let name = data.item.name
        if (data.item.vegi) { name += ' <span class="vegi">*</span>'}
        return name
      },
      handleEnter() {
        let searchText = this.search ? this.search.trim() : '';
        const box = this.$refs.newEntry
        let itemFound = box.filteredItems.length;
        if (!itemFound && searchText.length) {
          this.axios.post('meals/', {name: searchText})
            .then((firstResponse) => {
              this.store.loadItems()
              box.isMenuActive = false
              const plan = this.plan
              plan.meal = firstResponse.data
              plan.meal_id = firstResponse.data.id
              this.axios.put('plans/' + plan.id + '/', plan)
                .then(() => {this.$emit('reload-week')})
            })
        } else {
          this.handleTab()
        }
      },
      deleteMe() {
        this.axios.delete('plans/' + this.plan.id + '/')
            .then(() => {this.$emit('reload-week')})
      },
      updatePlan() {
        console.log("UPDATE PLAN")
        console.log(this.plan)
        if (!this.plan.meal) return;
        if (this.plan.meal_id !== this.plan.meal.id) {
          this.plan.meal_id = this.plan.meal.id
          this.plan.price = 0.00
        }
        this.axios.put('plans/' + this.plan.id + '/', this.plan)
            .then((response) => {this.plan = response.data})
      },
      switchHeadline() {
        const data = {headline: !this.plan.meal.headline}
        this.axios.patch('meals/' + this.plan.meal.id + '/', data)
        this.$emit('reload-week')
      },
      switchVegi() {
        const data = {vegi: !this.plan.meal.vegi, vegan: false}
        this.axios.patch('meals/' + this.plan.meal.id + '/', data)
        this.$emit('reload-week')
      },
      switchVegan() {
        const data = {vegan: !this.plan.meal.vegan, vegi: false}
        this.axios.patch('meals/' + this.plan.meal.id + '/', data)
        this.$emit('reload-week')
      }
    }
  }
</script>

<style lang="sass">
.left.bold
  font-weight: bold
.right.hidden
  opacity: 0
.v-btn.delete
  justify-self: end

.combobox
  display: grid
  grid-template-columns: 1fr 16px 16px
  grid-column-gap: 5px

.v-btn:before
  display: none
</style>
