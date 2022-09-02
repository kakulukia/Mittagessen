<template lang="pug">
.maelPlan {{ plan.meal.name }}
</template>

<script>
  export default {
    name: 'MealPlan',
    props: ['plan'],
    data () {
      return {
      }
    },
    created () {
    }
  }
</script>
