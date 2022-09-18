<template lang="pug">
.mealPlan
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
      @keydown.meta="checkBold($event)"
      :class="{'bold': plan.meal.headline}"
      tabindex="1"
    )
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
      }
    },
    created () {
    },
    methods: {
      deleteMe() {
        this.axios.delete('plans/' + this.plan.id + '/')
            .then(() => {this.$emit('reload-week')})
      },
      updatePlan() {
        if (this.plan.meal_id !== this.plan.meal.id) {
          this.plan.meal_id = this.plan.meal.id
          this.plan.price = 0.00
        }
        this.axios.put('plans/' + this.plan.id + '/', this.plan)
            .then((response) => {this.plan = response.data})
      },
      checkMeta(event) {
        this.$refs.newEntry.isMenuActive = false
        if (event.key === 'b') {
          const data = {headline: !this.plan.meal.headline}
          this.axios.patch('meals/' + this.plan.meal.id + '/', data)
          this.$emit('reload-week')
        }
        // if (event.key === 'ArrowUp') {
        //   this.axios.patch('plans/' + this.plan.id + '/', {order: this.plan.order + 1})
        //     .then(() => {this.$emit('reload-week')})
        // }
        // if (event.key === 'ArrowDown') {
        //   this.axios.patch('plans/' + this.plan.id + '/', {order: this.plan.order - 1})
        //     .then(() => {this.$emit('reload-week')})
        // }
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
</style>
