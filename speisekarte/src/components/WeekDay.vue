<template lang="pug">
  .weekDay
    h2 {{ day.dateDisplay }}
    MealPlan(v-for="plan in day.plans" :plan="plan" :key="plan.id")
</template>

<script>
  import MealPlan from '@/components/MealPlan'
  export default {
    name: 'WeekDay',
    components: {MealPlan},
    props: ['day'],
    data () {
      return {
      }
    },
    created () {
    }
  }
</script>
