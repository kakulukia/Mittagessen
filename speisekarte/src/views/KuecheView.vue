<template lang="pug">
div
  v-progress-linear(v-if="!week" color="red" indeterminate)
  .week(v-if="week")
    .menu-wrapper
      .container.speiseplan
        .menu
          span
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
              :href="apiHost + `?date=${this.week.start}`"
            )
              v-icon mdi-printer-outline
            //v-btn.print(
            //  icon target="_blank"
            //  :href="apiHost + '/admin/'"
            //)
              v-icon mdi-cog-outline
            v-btn.invoices(icon href="abrechnungen")
              v-icon mdi-invoice-text-edit-outline
          span
            v-btn(icon @click="switchWeek(true)")
              v-icon mdi-arrow-right-bold-circle-outline
    .container.speiseplan
      vue-editor.head(
          v-if="editHeadline"
          v-model="week.headline"
          :editor-toolbar="customToolbar"
          @text-change="updateHeadline()"
        )
      div.text-center.head(v-if="!editHeadline")
        img.logo(:src="apiHost + '/media/' + week.location_logo")
        div(v-html="week.headline")
        //div.green-text.bold Speiseplan in der Woche vom {{ week.days[0].dateDisplay }} - {{ week.days[week.days.length - 1].dateDisplay }}

      div
        a.green-text(:href="apiHost + '/admin/meals/suggestion/'" target="_blank") Essenswünsche: {{ suggestions }}
      br

      WeekDay(v-for="day in week.days" :key="day.id" :day="day" @reload-week="reloadWeek()")

      .footer
        vue-editor(
          v-if="editFooter"
          v-model="week.footer"
          :editor-toolbar="customToolbar"
          @text-change="updateFooter()"
        )
        div.text-center.footer(v-if="!editFooter" @click="editFooter=true") Tel.: 0152 / 27767327 Zusatzstoffe und Allergene bitte beim Personal erfragen
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
    inject: ['apiHost'],
    data () {
      return {
        week: null,
        date: undefined,
        editHeadline: false,
        editFooter: false,
        suggestions: 0,
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
      this.axios.get('unseen-suggestions').then((response) => {
        this.suggestions = response.data.count
      })

      this.reloadWeek()
    },
    methods: {
      reloadWeek() {
        this.axios.get('weeks/get-week/',{params: {date: this.isoDate}})
        .then((response) => {
          this.week = response.data
        })
      },
      switchWeek(next) {
        if (next) this.date = this.date.addDays(7)
        else this.date = this.date.addDays(-7)
        this.reloadWeek()
        // save the date as query parameter
        this.$router.push({query: {date: this.isoDate}})
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
  color: #BB171A
  font-weight: bold
  position: relative
  .imageHint
    position: absolute
    top: 0
    right: 0

img.logo
  height: 130px
  margin: 0 auto
  display: block

</style>
