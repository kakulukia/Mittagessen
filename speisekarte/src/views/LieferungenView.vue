<template lang="pug">
  .container
    v-row.my-5
      .v-col.auto.px-2
        v-btn(to="/abrechnungen") Zurück

    h1 Lieferungen und Bestellprüfung
    p.mb-6 Heutige Lieferungen und alle noch vorläufigen Bestelltage
    v-btn-toggle.mb-4(v-model="status" mandatory color="blue darken-3" aria-label="Bestellstatus filtern")
      v-btn(value="all" :aria-pressed="status === 'all' ? 'true' : 'false'") Alle
      v-btn(value="pending" :aria-pressed="status === 'pending' ? 'true' : 'false'") Vorläufig ({{ pendingCount }})
      v-btn(value="reviewed" :aria-pressed="status === 'reviewed' ? 'true' : 'false'") Abgenommen (heute)

    v-alert(v-if="error" type="error" dense role="alert") {{ error }}
    v-progress-linear(v-if="loading" indeterminate aria-label="Bestellungen werden geladen")
    div(v-else-if="visibleDays.length === 0 && !error") Keine Bestellungen für diesen Filter vorhanden.
    div(v-else-if="visibleDays.length")
      div {{ visibleDays.length }} {{ visibleDays.length === 1 ? 'Bestellung' : 'Bestellungen' }} bei {{ customerCount }} Kunden
      v-card.mt-4(v-for="day in visibleDays" :key="day.id" outlined)
        v-card-text
          v-row(align="center" dense)
            .col
              strong.text--primary {{ day.customer.name }}
              div {{ day.customer.short_address }}
              div {{ day.date | moment('dddd, DD.MM.YYYY') }}
            .col-auto
              v-chip(small outlined :color="day.reviewed ? 'green darken-3' : 'deep-orange darken-4'") {{ day.reviewed ? 'Abgenommen' : 'Vorläufig' }}
            .col-auto(v-if="day.reviewed")
              v-btn(
                :color="day.delivered ? 'success' : 'error'"
                :disabled="savingIds.includes(day.id)"
                :title="day.delivered ? 'Als noch nicht ausgeliefert markieren' : 'Als ausgeliefert markieren'"
                :aria-label="day.delivered ? 'Ausgeliefert' : 'Noch nicht ausgeliefert'"
                :aria-pressed="day.delivered ? 'true' : 'false'"
                @click="toggleDelivered(day)") ✓
          div.mt-4.text--primary
            div(v-for="meal in day.meals" :key="meal.id")
              div.meals
                span.text-right {{ meal.count }}x
                span
                  | {{ meal.name }}
                  span.red--text.text--darken-4.font-weight-bold.ml-2(v-if="meal.price_needs_review" title="Preis prüfen" role="img" aria-label="Preis prüfen") €?
              div.meals(v-if="meal.comment")
                strong.text-right Extra
                span {{ meal.comment }}
          div.mt-5.text--primary
            strong Originalnachricht
            div.original-message.mt-2 {{ day.source_message || 'Keine Originalnachricht hinterlegt.' }}
          v-btn.mt-4(
            v-if="!day.reviewed"
            color="green darken-3"
            outlined
            :disabled="savingIds.includes(day.id) || day.canReview === false"
            @click="reviewDay(day)"
          )
            v-icon(left) mdi-clipboard-check-outline
            | Als geprüft markieren
        v-expansion-panels(flat)
          v-expansion-panel
            v-expansion-panel-header Bearbeiten
            v-expansion-panel-content
              day-meal-editor(:day="day" :customer="day.customer" :show-delivery="false" @review-availability="$set(day, 'canReview', $event)" @update="loadInvoiceDays")
</template>

<script>
import DayMealEditor from '@/components/DayMealEditor'

export default {
  name: 'LieferungenView',
  components: { DayMealEditor },
  data() {
    return {
      invoiceDays: [],
      status: ['all', 'pending', 'reviewed'].includes(this.$route.query.status) ? this.$route.query.status : 'all',
      loading: true,
      error: '',
      savingIds: [],
    }
  },
  created() {
    this.loadInvoiceDays()
  },
  watch: {
    status(value) {
      if (this.$route.query.status !== value) {
        this.$router.replace({ query: { ...this.$route.query, status: value } })
      }
    },
  },
  methods: {
    async reviewDay(day) {
      if (day.canReview === false || this.savingIds.includes(day.id)) return
      this.savingIds.push(day.id)
      this.error = ''
      try {
        const response = await this.axios.patch(`invoice-days/${day.id}/`, { reviewed: true })
        day.reviewed = response.data.reviewed
        day.meals = response.data.meals
      } catch (error) {
        const data = error.response && error.response.data
        this.error = data && typeof data === 'object' ? Object.values(data).flat().join(' ') : ''
        this.error = this.error || 'Prüfstatus konnte nicht gespeichert werden. Bitte erneut versuchen.'
      } finally {
        this.savingIds = this.savingIds.filter(id => id !== day.id)
      }
    },
    async toggleDelivered(day) {
      this.savingIds.push(day.id)
      this.error = ''
      try {
        const response = await this.axios.patch(`invoice-days/${day.id}/`, { delivered: !day.delivered })
        day.delivered = response.data.delivered
      } catch (error) {
        this.error = 'Lieferstatus konnte nicht gespeichert werden. Bitte erneut versuchen.'
      } finally {
        this.savingIds = this.savingIds.filter(id => id !== day.id)
      }
    },
    async loadInvoiceDays() {
      this.loading = true
      this.error = ''
      try {
        const response = await this.axios.get('/invoice-days/deliveries/')
        this.invoiceDays = response.data.map(day => ({ ...day, date: new Date(`${day.date}T00:00:00`) }))
      } catch (error) {
        this.error = 'Bestellungen konnten nicht geladen werden. Bitte die Seite neu laden.'
      } finally {
        this.loading = false
      }
    },
  },
  computed: {
    pendingCount() {
      return this.invoiceDays.filter(day => !day.reviewed).length
    },
    visibleDays() {
      const today = new Date().toDateString()
      return this.invoiceDays.filter(day => {
        if (this.status === 'pending') return !day.reviewed
        if (this.status === 'reviewed') return day.reviewed && day.date.toDateString() === today
        return !day.reviewed || day.date.toDateString() === today
      })
    },
    customerCount() {
      return new Set(this.visibleDays.map(day => day.customer.id)).size
    },
  },
}
</script>

<style scoped lang="sass">
.original-message
  white-space: pre-wrap
  overflow-wrap: anywhere

.meals
  display: grid
  grid-template-columns: 40px 1fr
  grid-gap: 10px
</style>
