<template lang="pug">
  .container
    v-dialog(max-width="500" v-model="showInvoiceTextDialog")
      template(v-slot:default="{ isActive }")
        v-card
          v-card-title Rechnungstext
          v-card-text

            v-textarea(v-model="invoiceText" rows="2" auto-grow)

          v-card-actions
            v-spacer

            v-btn(@click="showInvoiceTextDialog = false") Abbrechen
            v-btn(@click="generateNewInvoice()" color="primary") Rechnung erstellen

    v-row.my-5(v-if="!selectedCustomer")
      .v-col.auto.px-2
        v-btn(href="lieferungen") Aktuelle Lieferungen
          v-icon mdi-truck-fast
      .v-col.auto.px-2
        v-btn(href="rechnungen") Alle Rechnungen
          v-icon mdi-file-document-multiple-outline
      .v-col.auto.px-2
        v-btn(:to="{ name: 'Kueche' }") Küche
          v-icon mdi-silverware-variant

    h1(v-if="!selectedCustomer") Kundenübersicht
    .overview(v-if="selectedCustomer")
      v-row
        .col
          h1 {{ selectedCustomer.name }}
            v-btn(@click="resetView()" icon)
              v-icon mdi-close
        .col-auto
          v-btn(@click="showInvoices = false") Tagesansicht
            v-icon mdi-calendar-blank
        .col-auto
          v-btn(@click="loadInvoices()" ) Alte Rechnungen
            v-icon mdi-invoice-text-clock-outline
        .col-auto
          v-btn(@click="prepareInvoiceText()") Neue Rechnung
            v-icon mdi-invoice-text-plus-outline

      .invoices(v-if="showInvoices")
        div Rechnungen
        br
        div(v-if="invoices.length === 0") Keine Rechnungen vorhanden
        v-list(v-if="invoices.length !== 0")
          v-list-item(v-for="invoice in invoices" :key="invoice.id")
            v-list-item-content
              v-list-item-title {{ invoice.invoice_number }} ({{ invoice.date}})
              v-list-item-subtitle {{ invoice.total }} €
            v-list-item-action
              v-btn-toggle(dense borderless)
                v-btn
                  a(:href="`${apiHost}/api/invoices/${invoice.id}/pdf/`" target="_blank") Rechnung Runterladen
                    v-icon mdi-file-download-outline

      .days(v-if="!showInvoices")
        div Tagesübersicht
        br

        day-meal-editor(v-for="day in days.filter(d => !d.invoice)" :day="day" :customer="selectedCustomer" @update="loadInvoiceDays" :key="day.id")

        br
        v-btn-toggle(dense borderless)
          v-btn(@click="createNewDay()" v-if="!newDay.date") +

        day-meal-editor(
          v-if="newDay.date"
          :day="newDay"
          :customer="selectedCustomer"
          @new-day-created="newDayCreated()"
          :blockedTimes="blockedTimes"
          @update="loadInvoiceDays()"
        )


    .customers(v-if="!editCustomer && !selectedCustomer")

      v-row(align="center")
        .col
          v-text-field(label="Suche" v-model="search" append-icon="mdi-magnify" clearable)
        .col-auto
          v-btn-toggle(dense borderless)
            v-btn(@click="create") Neu

      v-list.customerList
        v-list-item.customer(v-for="customer in filteredCustomers" :key="customer.id")
          v-list-item-icon.pointer(@click="selectCustomer(customer)")
            v-icon(v-if="customer.delivery_type === 'delivery'") mdi-truck-delivery-outline
            v-icon(v-if="customer.delivery_type === 'takeaway'") mdi-food-takeout-box-outline
          v-list-item-content.pointer(@click="selectCustomer(customer)")
            v-list-item-title {{ customer.name }}
            v-list-item-subtitle {{ customer.short_address }}
              br
              | {{ customer.bank_account === 'bank' ? 'Sparkasse' : 'SumUp' }}
          v-list-item-action
            v-btn-toggle(dense borderless)
              v-btn(@click="setCustomer(customer)" @clicik.stop="true")
                v-icon mdi-pencil


    .newCustomer(v-if="editCustomer")
      h4(v-if="!newCustomer.id") Neuen Kunden anlegen
      h4(v-if="newCustomer.id") Kunden bearbeiten
      br
      br

      v-textarea(label="Adresse" rows="4" v-model="newCustomer.address")
      v-text-field(label="eMail" v-model="newCustomer.email")
      v-radio-group(inline v-model="newCustomer.delivery_type")
        v-radio(label="Belieferung" value="delivery")
        v-radio(label="Selbstabholer" value="takeaway")
      v-radio-group(inline v-model="newCustomer.bank_account" label="Zahlungsart")
        v-radio(label="Sparkasse" value="bank")
        v-radio(label="SumUp" value="sumup")

      v-row.mt-4
        .col-auto
          v-btn(@click="saveCustomer") Speichern
        .col-auto
          v-btn(@click="editCustomer = false") Abbrechen

</template>

<script>
import DayMealEditor from '@/components/DayMealEditor';

export default {
  name: 'AbrechnungenView',
  inject: ['apiHost'],
  components: {
    DayMealEditor,
  },
  data () {
      return {
        editCustomer: false,
        newCustomer: {
          address: '',
          email: '',
          delivery_type: '',
        },
        customers: [],
        selectedCustomer: null,
        search : '',
        days: [],
        newDay: {
          date: '',
          delivered: false,
          combining_dates: false,
        },
        toggle_exclusive: 2,
        showInvoices: false,
        invoices: [],
        invoiceText: '',
        showInvoiceTextDialog: false,
      }
    },

  created () {
     this.loadCustomers()
  },
  methods: {
    prepareInvoiceText() {

      const unbilledDays = this.days.filter(day => day.invoice === null)

      if (unbilledDays.length === 0) {
        alert("Es gibt keine nicht abgerechneten Tage für eine neue Rechnung.")
        return
      }
      const invoiceDay = unbilledDays[0]
      const invoiceDate = new Date(invoiceDay.date)
      const month = invoiceDate.toLocaleString('default', { month: 'long' })
      const year = invoiceDate.getFullYear()
      this.invoiceText = `Mittagessen für den Monat ${month} ${year}`

      console.log("prepareInvoiceText")
      this.showInvoiceTextDialog = true
    },
    generateNewInvoice() {

      this.axios.post(`/customers/${this.selectedCustomer.id}/generate-invoice/`, {invoiceText: this.invoiceText})
        .then((response) => {
          let invoice_id = response.data.invoice_id
          window.open(`${this.apiHost}/api/invoices/${invoice_id}/pdf/`, '_blank')
          this.loadInvoiceDays()
        }).catch((error) => {
          let message = error.response.data.message
          alert(message)
        });
    },
    setCustomer(customer) {
      this.newCustomer = customer
      this.editCustomer = true
    },
    resetView() {
      this.selectedCustomer = null
      this.showInvoices = false
      this.newDay = {
        date: '',
        delivered: false,
        combining_dates: false,
      }
    },
    loadInvoices() {
      this.showInvoices = true
      this.axios.get(`/customers/${this.selectedCustomer.id}/invoices/`)
        .then(response => {
          this.invoices = response.data
        })
    },
    selectCustomer(customer) {
      this.selectedCustomer = customer
      this.loadInvoiceDays()
    },
    loadInvoiceDays() {
      this.axios.get(`/customers/${this.selectedCustomer.id}/invoice-days/`)
        .then(response => {
          let days = response.data;

          // convert all dates to Date objects
          days.forEach(day => {
            day.date = new Date(day.date)
          })
          this.days = days

        })
        .catch(error => {
          console.error("Fehler beim Laden der Invoice Days:", error);
        });
    },
    create() {
      this.editCustomer = true
      this.newCustomer = {
        address: '',
        email: '',
        deliveryType: '',
      }
    },
    createNewDay() {
      this.loadInvoiceDays()
      this.newDay = {
        date: new Date(),
        delivered: false,
        combining_dates: false,
      }

      // check if days contains the current date
      // while this is true add a day to the date
      while (this.days.find(day => day.date.toISODate() === this.newDay.date.toISODate())) {
        this.newDay.date.setDate(this.newDay.date.getDate() + 1);
      }


    },
    newDayCreated() {
      console.log("newDayCreated")
      this.newDay = {
        date: '',
        delivered: false,
        combining_dates: false,
      }
      this.loadInvoiceDays()
    },
    resetCustomer() {
      this.editCustomer = false
      this.newCustomer = {
        address: '',
        email: '',
        deliveryType: '',
      }
    },
    saveCustomer() {
      if (this.newCustomer.id) {
        this.axios.put(`customers/${this.newCustomer.id}/`, this.newCustomer)
          .then(() => {
            this.resetCustomer()
            this.loadCustomers()
          })
      } else {
        this.axios.post('customers/', this.newCustomer)
          .then(() => {
            this.resetCustomer()
            this.loadCustomers()
          })
      }
    },
    loadCustomers() {
      this.axios.get('customers/', ).then((response) => {
         this.customers = response.data
     })
    },
  },
  computed: {
    filteredCustomers() {
      if (this.search === "") {
        return this.customers
      }
      // Return filtered customers based on search input
      return this.customers.filter(customer =>
        customer.address.toLowerCase().includes(this.search.toLowerCase())
      );
    },
    blockedTimes() {
      if (!this.days) return []
      return this.days.map(day => {
        const d = new Date(day.date);
        return day.combining_dates ? d.toISOMonth() : d.toISODate()
      });
    }
  },
};
</script>

<style scoped lang="sass">
.v-btn.delivery
  color: lightgray
  &.delivered
    color: green
.customer:hover
  background-color: #f0f0f0

.pointer
  cursor: pointer

.auslieferung
  position: fixed
  bottom: 50px
  right: 50px
  .v-icon
    font-size: 50px

.v-btn .v-icon
  padding: 0 5px

</style>
