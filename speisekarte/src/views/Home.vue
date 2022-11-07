<template lang="pug">
.week(v-if="week")
  .menu-wrapper
    .container.speiseplan
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
          v-btn.print(
            icon v-if="week.published" target="_blank"
            :href="this.$root.apiHost + '?date=' + this.week.start"
          )
            v-icon mdi-printer-outline
          v-btn.print(
            icon target="_blank"
            :href="this.$root.apiHost + '/admin/'"
          )
            v-icon mdi-cog-outline
        v-btn(icon @click="switchWeek(true)")
          v-icon mdi-arrow-right-bold-circle-outline
  .container.speiseplan
    vue-editor.head(
        v-if="editHeadline"
        v-model="week.headline"
        :editor-toolbar="customToolbar"
        @text-change="updateHeadline()"
      )
    div.text-center.head(v-if="!editHeadline" @click="editHeadline=true")
      div(v-html="week.headline")
      div.green-text.bold Speiseplan in der Woche vom 26.09. - 30.09.2022

    WeekDay(v-for="day in week.days" :key="day.id" :day="day" @reload-week="reloadWeek()")

    .footer
      vue-editor(
        v-if="editFooter"
        v-model="week.footer"
        :editor-toolbar="customToolbar"
        @text-change="updateFooter()"
      )
      div.text-center.footer(v-if="!editFooter" v-html="week.safe_footer" @click="editFooter=true")
      v-btn.imageHint(
          icon v-if="!editFooter && week.background"
          @click="editFooter=true"
        )
          v-icon mdi-file-image

</template>

<script>
import WeekDay from '@/components/WeekDay'

  export default {
    name: 'Home',
    components: {WeekDay},
    data () {
      return {
        week: null,
        date: undefined,
        editHeadline: false,
        editFooter: false,
        customToolbar: [
          ["bold", "italic", "image", { 'color': [] }, { 'align': [] }],
          // [{ list: "ordered" }, { list: "bullet" }],
        ]
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
        const week = this.week
        this.axios.patch(`weeks/${week.id}/ `, {published: week.published})
          .catch((error) => {
            alert(error.response.data.non_field_errors)
            window.location.reload()
          })
      },
      updateFooter() {
        this.axios.patch(`weeks/${this.week.id}/`, {footer: this.week.footer})
      },
      updateHeadline() {
        this.axios.patch(`weeks/${this.week.id}/`, {headline: this.week.headline})
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

.print
  margin-left: 10px

.v-application p
  margin-bottom: 0

.head, .footer
  margin-bottom: 1em
.bold
  font-weight: bold

.footer
  position: relative
  .imageHint
    position: absolute
    top: 0
    right: 0

</style>
