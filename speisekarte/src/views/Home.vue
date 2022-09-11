<template lang="pug">
.container(v-if="week" )
  .menu
    v-btn(icon @click="switchWeek(false)")
      v-icon mdi-arrow-left-bold-circle-outline
    h1 Woche vom {{ week.dateDisplay}} (KW {{ week.kw }})
    v-btn(icon @click="switchWeek(true)")
      v-icon mdi-arrow-right-bold-circle-outline
  WeekDay(v-for="day in week.days" :key="day.id" :day="day" @reload-week="reloadWeek()")
</template>

<script>
import WeekDay from '@/components/WeekDay'

  export default {
    name: 'Home',
    components: {WeekDay},
    data () {
      return {
        week: null,
        date: undefined
      }
    },
    created () {
      if (this.$route.query.date) {
        this.date = new Date(this.$route.query.date)
      } else {
        this.date = new Date()
      }
      this.reloadWeek()
    },
    methods: {
      reloadWeek() {
        this.axios.get('weeks/get-week/',{params: {date: this.date}})
        .then((response) => {
          this.week = response.data
        })
      },
      switchWeek(next) {
        if (next) this.date = this.date.addDays(7)
        else this.date = this.date.addDays(-7)
        this.reloadWeek()
      }
    },
    computed: {
      isoDate () {
        return this.date.toISODate()
      }
    }
  }
</script>

<style lang="sass">
.menu
  display: flex
  justify-content: space-between
</style>
