<template lang="pug">
  .container
    h1(v-if="!selectedCustomer") Kundenübersicht
    .overview(v-if="selectedCustomer")
      h1 {{ selectedCustomer.name }}
        v-btn(@click="selectedCustomer = null" icon)
          v-icon mdi-close
      .days
        div Tagesübersicht
        br

        day-meal-editor(v-for="day in days" :day="day" :customer="selectedCustomer" @update="loadInvoiceDays" :key="day.id")

        v-btn-toggle(dense borderless)
          v-btn(@click="createNewDay()" v-if="!newDay.date") +

        day-meal-editor(
          v-if="newDay.date"
          :day="newDay"
          :customer="selectedCustomer"
          @new-day-created="newDayCreated"
          :blockedTimes="blockedTimes"
        )


    .customers(v-if="!createNewCustomer && !selectedCustomer")

      v-row(align="center")
        .col
          v-text-field(label="Suche" v-model="search" append-icon="mdi-magnify" clearable)
        .col-auto
          v-btn-toggle(dense borderless)
            v-btn(@click="create") Neu

      v-list
        v-list-item.customer(v-for="customer in filteredCustomers" :key="customer.id" @click="selectCustomer(customer)")
          v-list-item-icon
            v-icon(v-if="customer.delivery_type === 'delivery'") mdi-truck-delivery-outline
            v-icon(v-if="customer.delivery_type === 'takeaway'") mdi-food-takeout-box-outline
          v-list-item-content
            v-list-item-title {{ customer.name }}
            v-list-item-subtitle {{ customer.email }}



    .newCustomer(v-if="createNewCustomer")
      h4 Neuen Kunden anlegen
      v-textarea(label="Adresse" rows="4" v-model="newCustomer.address")
      v-text-field(label="eMail" v-model="newCustomer.email")
      // wee need radio otion for delivery type
      v-radio-group(inline v-model="newCustomer.delivery_type")
        v-radio(label="Beliefernug" value="delivery")
        v-radio(label="Selbstabholer" value="takeaway")
      v-row
        .col-auto
          v-btn(@click="addCustomer") Anlegen
        .col-auto
          v-btn(@click="createNewCustomer = false") Abbrechen

</template>

<script>
import DayMealEditor from '@/components/DayMealEditor';

export default {
  name: 'AbrechnungenView',
  components: {
    DayMealEditor,
  },
  data () {
      return {
        createNewCustomer: false,
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
      }
    },

  created () {
     this.loadCustomers()
  },
  methods: {
    selectCustomer(customer) {
      this.selectedCustomer = customer
      this.loadInvoiceDays()
    },
    loadInvoiceDays() {
      console.log('loadInvoiceDays')
      this.axios.get(`/customers/${this.selectedCustomer.id}/invoice-days/`)
        .then(response => {
          this.days = response.data;

          // convert all dates to Date objects
          this.days.forEach(day => {
            day.date = new Date(day.date);
          });

        })
        .catch(error => {
          console.error("Fehler beim Laden der Invoice Days:", error);
        });
    },
    create() {
      this.createNewCustomer = true
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
      console.log('newDayCreated')
      this.newDay = {
        date: '',
        delivered: false,
        combining_dates: false,
      }
      this.loadInvoiceDays()
    },
    addCustomer() {
      this.axios.post('customers/', this.newCustomer)
        .then((response) => {
          this.createNewCustomer = false
          this.newCustomer = {
            address: '',
            email: '',
            deliveryType: '',
          }

          this.loadCustomers()
          this.selectedCustomer = response.data
        })
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
        customer.name.toLowerCase().includes(this.search.toLowerCase())
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
</style>
