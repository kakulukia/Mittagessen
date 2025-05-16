<template lang="pug">
  .container

    v-row.my-5
      .v-col.auto.px-2
        v-btn(to="/abrechnungen") Zurück

    h1 Rechnungsübersicht

    div(v-if="invoices.length === 0") Keine Rechnungen vorhanden
    v-list(v-if="invoices.length !== 0")
      v-list-item(v-for="invoice in invoices" :key="invoice.id")
        v-list-item-content
          v-list-item-title {{ invoice.invoice_number }} ({{ invoice.date}})
          v-list-item-subtitle {{ invoice.total }} € - {{ invoice.customer_name }}
        v-list-item-action
          v-btn-toggle(dense borderless)
            v-btn(:to="`/abrechnungen/${invoice.id}`")
              v-icon mdi-pencil
            v-btn(:href="`${apiHost}/api/invoices/${invoice.id}/pdf/`" target="_blank")
              | Rechnung Herunterladen
              v-icon mdi-file-download-outline

</template>

<script>
export default {
  name: 'RechnungenView',
  inject: ['apiHost'],
  data () {
      return {
        invoices: [],
      }
    },

  created () {
     this.loadInvoices()
  },
  methods: {
    loadInvoices() {
      this.axios.get(`/invoices/`)
        .then(response => {
          this.invoices = response.data;
        })
    },
  },
  computed: {
  },
};
</script>

<style scoped lang="sass">
:deep(.v-list-item)
  transition: background-color .3s
  &:hover
    background-color: rgba(0, 0, 0, 0.04)
</style>
