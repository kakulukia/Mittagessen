<template lang="pug">
.week
  .menu-wrapper
    .container(v-if="week" )
      .menu
        v-btn(icon @click="switchWeek(false)")
          v-icon mdi-arrow-left-bold-circle-outline
        h1 KW{{ week.kw }}
          v-checkbox(
            v-model="week.published"
            label="freigegeben"
            dense
            hide-details
            :success="week.published"
            :error="!week.published"
            @click="updatePublished()"
          )
        v-btn(icon @click="switchWeek(true)")
          v-icon mdi-arrow-right-bold-circle-outline
  .container
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
      },
      updatePublished() {
        this.axios.patch(`weeks/${this.week.id}/ `, {published: this.week.published})
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
  align-items: center
.menu-wrapper
  border-bottom: 2px solid #ddd
h1
  display: flex
  align-items: center
  .v-input--checkbox.v-input--dense
    margin-top: 0
    padding-top: 0
    margin-left: 1em
</style>
