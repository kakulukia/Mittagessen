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
    )
  v-text-field.right(v-model="plan.price"
    hide-details
    single-line
    type="number"
    dense
    @change="updatePlan()"
  )
    v-icon(slot="append") mdi-currency-eur

  v-btn(icon color="red darken-4" @click="deleteMe()")
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
      }
    }
  }
</script>

<style lang="sass">
.mealPlan
  display: grid
  grid-template-columns: 1fr 80px 50px
  column-gap: 20px
</style>
