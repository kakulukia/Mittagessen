<template lang="pug">
.container(v-if="week" )
  h1 Woche vom {{ week.dateDisplay}} (KW {{ week.kw }})
  WeekDay(v-for="day in week.days" :key="day.id" :day="day")
</template>

<script>
import WeekDay from '@/components/WeekDay'

  export default {
    name: 'Home',
    components: {WeekDay},
    data () {
      return {
        week: null,
      }
    },
    created () {
      this.axios.get('weeks/current-week/')
        .then((response) => {
          this.week = response.data
        })
    }
  }
</script>
