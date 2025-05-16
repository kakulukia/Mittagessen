<template lang="pug">
  .container
    v-row.my-5
      .v-col.auto.px-2
        v-btn(to="/rechnungen") Zurück
    h1 Rechnung bearbeiten

    v-form(ref="form")
      p.mt-5 Rechnungsummer: {{ invoice.invoice_number }}
      p.mb-5 Empfänger: {{ invoice.customer_name }}
      v-textarea(v-model="invoice.text" label="Rechnungstext" rows="2" auto-grow)

      div.mt-4(v-for="day in invoiceDays" :key="day.id")
        v-header.bold {{ day.date }}
        v-list
          v-list-item(v-for="meal in day.meals" :key="meal.id")
            v-list-item-content
              v-row
                v-col(cols="2")
                  v-text-field(v-model="meal.count" label="Anzahl" type="number" hide-details)
                v-col(cols="8")
                  v-text-field(v-model="meal.name" label="Beschreibung" hide-details)
                v-col(cols="2")
                  v-text-field(v-model="meal.price" label="Preis" type="number" hide-details)
      v-row.gap.mt-4
        .v-col-auto
          v-btn(color="primary" @click="save") Speichern
        .v-col-auto
          v-btn
            a(:href="`${apiHost}/api/invoices/${invoice.id}/pdf/`" target="_blank" icon) Rechnung Herunterladen
              v-icon mdi-file-download-outline
</template>

<script>
export default {
  name: 'RechnungEditView',
  inject: ['apiHost'],
  data() {
    return {
      invoice: {},
      invoiceDays: [],
    };
  },
  created() {
    this.loadData();
  },
  methods: {
    loadData() {
      const id = this.$route.params.id;
      this.axios.get(`/invoices/${id}/`)
        .then(response => { this.invoice = response.data; });
      this.axios.get(`/invoices/${id}/days/`)
        .then(response => { this.invoiceDays = response.data; });
    },
    save() {
      const id = this.$route.params.id;
      this.axios.patch(`/invoices/${id}/`, { text: this.invoice.text });
      this.invoiceDays.forEach(day => {
        day.meals.forEach(meal => {
          this.axios.patch(`/invoice-meals/${meal.id}/`, {
            count: meal.count,
            name: meal.name,
            price: meal.price,
          });
        });
      });
    },
  },
};
</script>

<style scoped lang="sass">
:deep(.v-list-item)
  transition: background-color .3s
  &:hover
    background-color: rgba(0,0,0,0.04)
.row.gap
  column-gap: 16px
</style>
