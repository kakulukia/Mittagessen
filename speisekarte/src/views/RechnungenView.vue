<template lang="pug">
  .container
    v-row.my-5
      .v-col.auto.px-2
        v-btn(to="/abrechnungen") Zurück

    h1.mb-4 Rechnungsübersicht

    v-alert(v-if="error" type="error" outlined)
      | Rechnungen konnten nicht geladen werden.
      v-btn.ml-2(text @click="loadInvoices") Erneut versuchen
    v-progress-linear(v-if="loading" indeterminate aria-label="Rechnungen werden geladen")

    template(v-if="!loading && !error")
      v-row
        v-col(cols="12" sm="5")
          v-select(v-model="selectedMonth" :items="monthOptions" label="Liefermonat" outlined dense hide-details)
        v-col(cols="12" sm="7")
          v-text-field(v-model="search" label="Kunde suchen" prepend-inner-icon="mdi-magnify" clearable outlined dense hide-details)

      v-alert.mt-4(v-if="unassignedCount" type="warning" outlined)
        | Bei {{ unassignedCount }} Rechnungen fehlt ein eindeutiger Liefermonat. Bitte unter „Monatszuordnung prüfen“ kontrollieren.

      v-card.my-4(outlined)
        v-card-text
          h2.text-subtitle-1.font-weight-bold.mb-3 {{ summaryTitle }}
          v-row
            v-col(cols="6" sm="3")
              div Rechnungen
              strong.text-h6 {{ filteredInvoices.length }}
            v-col(cols="6" sm="3")
              div Netto
              strong.text-h6 {{ formatAmount(totals.net) }}
            v-col(cols="6" sm="3")
              div MwSt.
              strong.text-h6 {{ formatAmount(totals.tax) }}
            v-col(cols="6" sm="3")
              div Brutto
              strong.text-h6 {{ formatAmount(totals.total) }}
          p.mt-3.mb-0(v-if="Object.values(totals).includes(null)") Summen unvollständig: Bei mindestens einer Rechnung fehlt ein Betrag.
          p.mt-3.mb-0(v-if="searchTerm") Die Summen beziehen sich auf alle gefundenen Kundenrechnungen im gewählten Zeitraum.

      p(v-if="searchTerm" role="status") {{ filteredInvoices.length }} von {{ monthInvoices.length }} Rechnungen gefunden.
      p(v-if="!invoices.length" role="status") Keine Rechnungen vorhanden.
      p(v-else-if="!filteredInvoices.length" role="status") Keine Rechnungen für diese Auswahl gefunden.

      .d-flex.flex-wrap.align-center.justify-space-between(v-if="filteredInvoices.length")
        p.mb-2.mb-sm-0(role="status") Rechnungen {{ (page - 1) * pageSize + 1 }} bis {{ Math.min(page * pageSize, filteredInvoices.length) }} von {{ filteredInvoices.length }}
        v-pagination(v-if="pageCount > 1" v-model="page" :length="pageCount" :total-visible="5")

      v-list(v-if="filteredInvoices.length")
        v-list-item.px-0(v-for="invoice in paginatedInvoices" :key="invoice.id")
          v-list-item-content
            v-list-item-title.font-weight-medium {{ invoice.customer_name }}
            v-list-item-subtitle {{ invoice.invoice_number }} · {{ formatDate(invoice.date) }} · {{ formatAmount(invoice.total) }}
            v-list-item-subtitle Liefermonat: {{ deliveryMonthLabel(invoice) }}
          v-list-item-action
            .d-flex
              v-btn(icon :to="`/abrechnungen/${invoice.id}`" :aria-label="`Rechnung ${invoice.invoice_number} bearbeiten`" title="Rechnung bearbeiten")
                v-icon mdi-pencil
              v-btn(icon :href="`${apiHost}/api/invoices/${invoice.id}/pdf/`" target="_blank" :aria-label="`Rechnung ${invoice.invoice_number} herunterladen`" title="Rechnung herunterladen")
                v-icon mdi-file-download-outline
</template>

<script>
export default {
  name: 'RechnungenView',
  inject: ['apiHost'],
  data () {
    return {
      invoices: [],
      selectedMonth: '',
      search: '',
      page: 1,
      pageSize: 20,
      loading: true,
      error: false,
    }
  },
  created () {
    this.loadInvoices()
  },
  watch: {
    filteredInvoices() {
      this.page = 1
    },
  },
  methods: {
    async loadInvoices() {
      this.loading = true
      this.error = false
      try {
        const response = await this.axios.get('/invoices/')
        this.invoices = response.data
        this.selectedMonth = this.availableMonths[0] || (this.unassignedCount ? 'unassigned' : '')
      } catch (error) {
        this.error = true
      } finally {
        this.loading = false
      }
    },
    monthLabel(month) {
      return new Date(`${month}-01T12:00:00`).toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })
    },
    deliveryMonthLabel(invoice) {
      if (!invoice.delivery_months.length) return 'Fehlt'
      return invoice.delivery_months.map(this.monthLabel).join(', ')
    },
    formatDate(value) {
      return new Date(`${value}T12:00:00`).toLocaleDateString('de-DE')
    },
    formatAmount(value) {
      if (value === null || value === '' || !Number.isFinite(Number(value))) return 'Unvollständig'
      return Number(value).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })
    },
  },
  computed: {
    availableMonths() {
      return [...new Set(this.invoices.filter(invoice => invoice.delivery_months.length === 1)
        .map(invoice => invoice.delivery_months[0]))].sort().reverse()
    },
    unassignedCount() {
      return this.invoices.filter(invoice => invoice.delivery_months.length !== 1).length
    },
    monthOptions() {
      const options = [{ text: 'Alle Monate', value: '' },
        ...this.availableMonths.map(month => ({ text: this.monthLabel(month), value: month }))]
      if (this.unassignedCount) options.push({ text: 'Monatszuordnung prüfen', value: 'unassigned' })
      return options
    },
    monthInvoices() {
      return this.invoices.filter(invoice => {
        if (!this.selectedMonth) return true
        if (this.selectedMonth === 'unassigned') return invoice.delivery_months.length !== 1
        return invoice.delivery_months.length === 1 && invoice.delivery_months[0] === this.selectedMonth
      })
    },
    searchTerm() {
      return (this.search || '').trim().toLocaleLowerCase('de-DE')
    },
    filteredInvoices() {
      return this.monthInvoices.filter(invoice => invoice.customer_name.toLocaleLowerCase('de-DE').includes(this.searchTerm))
    },
    pageCount() {
      return Math.ceil(this.filteredInvoices.length / this.pageSize)
    },
    paginatedInvoices() {
      const start = (this.page - 1) * this.pageSize
      return this.filteredInvoices.slice(start, start + this.pageSize)
    },
    summaryTitle() {
      if (!this.selectedMonth) return 'Gesamtsumme aller Monate'
      if (this.selectedMonth === 'unassigned') return 'Summe ohne eindeutige Monatszuordnung'
      return `Monatssumme: ${this.monthLabel(this.selectedMonth)}`
    },
    totals() {
      const totals = {}
      for (const field of ['net', 'tax', 'total']) {
        totals[field] = this.filteredInvoices.some(invoice => invoice[field] === null || invoice[field] === '' || !Number.isFinite(Number(invoice[field])))
          ? null
          : this.filteredInvoices.reduce((sum, invoice) => sum + Math.round(Number(invoice[field]) * 100), 0) / 100
      }
      return totals
    },
  },
}
</script>

<style scoped lang="sass">
.v-list-item__title, .v-list-item__subtitle
  white-space: normal
.v-list-item:hover
  background-color: rgba(0, 0, 0, 0.04)
</style>
