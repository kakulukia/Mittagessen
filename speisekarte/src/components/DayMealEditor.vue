<template lang="pug">
  .day(v-if="day.date")
    v-row(align="center" dense)
      .col
        strong {{ formattedDate }}
      .col-auto
        v-btn-toggle(dense borderless v-if="!day.id")
          v-btn(@click="subtractFromDay")
            v-icon mdi-chevron-up
          v-btn(@click="addToDay")
            v-icon mdi-chevron-down
      .col-auto
        v-btn-toggle(dense borderless)
          v-btn(
            v-if="!day.id"
            :color="day.combining_dates ? 'primary' : 'default'"
            @click="toggleCombiningDates(day)"
          )
            v-icon mdi-calendar-month-outline
          v-btn.delivery(
            v-if="day.id"
            :class="{delivered: day.delivered}"
            @click="toggleDelivered") ✓

    // show existing meals
    v-row.meals(align="center" dense v-for="meal in day.meals" :key="meal.id")
      .col
        v-select(
          :items="mealItems"
          label="Gericht"
          v-model="meal.name"
          @blur="updateMeal(meal)"
          hide-details
        )
      .col-2
        v-combobox(
          v-model="meal.count"
          :items="countItems"
          label="Anzahl"
          type="number"
          min="1"
          hide-details
          @blur="updateMeal(meal)"
        )
      .col-2
        v-text-field(
          v-model="meal.price"
          label="Preis"
          type="number"
          min="0"
          step="0.50"
          suffix="€"
          @blur="updateMeal(meal)"
          hide-details
        )
      .col-auto
        v-btn-toggle(dense borderless)
          v-btn.delivery(
            :class="{delivered: meal.delivered}"
            @click="toggleMealDelivered(meal); updateMeal(meal)"
          ) ✓


    // add option to add a new meal
    v-row(align="center" dense)
      .col
        v-select(
          :items="mealItems"
          label="Gericht"
          v-model="newMeal.name"
          @blur="updateMeal(newMeal)"
        )
      .col-2
        v-combobox(
          v-model="newMeal.count"
          :items="countItems"
          label="Anzahl"
          type="number"
          min="1"
          dense
          hide-details
          @blur="updateMeal(newMeal)"
        )
      .col-2
        v-text-field(
          v-model="newMeal.price"
          label="Preis"
          type="number"
          min="0"
          step="0.50"
          suffix="€"
          @blur="updateMeal(newMeal)"
        )
      .col-auto
        .spacer-delivered
</template>

<script>
export default {
  name: 'DayMealEditor',
  props: {
    // Der Tag, der entweder neu (ohne id) oder bereits bestehend ist
    day: {
      type: Object,
      required: true
    },
    // Aktuell ausgewählter Kunde
    customer: {
      type: Object,
      required: true
    },
    blockedTimes: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      // Formularzustand für ein neues Meal – immer pro Tag vorhanden
      newMeal: {
        name: '',
        count: 1,
        price: '',
        delivered: false,
        // day wird später gesetzt via: this.newMeal.day = this.day.id
      },
      // Auswahlmöglichkeiten für Gerichte
      mealItems: ['Mittagessen', 'Mittagessen 2', 'Eintopf', 'Nachtisch'],
      // Auswahlmöglichkeiten für die Anzahl
      countItems: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
  },
  computed: {
    // Computed, um zu gewährleisten, dass wenn day.delivered gesetzt wird,
    // alle Meals (und newMeal) ebenfalls delivered true haben
    allMealsDelivered: {
      get() {
        return this.day.delivered;
      },
      set(val) {
        // Setze delivered beim Tag
        this.day.delivered = val;
        // Falls bereits eine Liste von Meals vorhanden ist, aktualisiere diese
        if (this.day.meals && this.day.meals.length) {
          this.day.meals.forEach(meal => {
            meal.delivered = val;
            this.updateMeal(meal);
          });
        }
      }
    },
    formattedDate() {
      if (!this.day.combining_dates) {
        return this.day.date.toLocaleDateString('de-DE', {
          weekday: 'short',
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        })
      } else {
        return this.day.date.toLocaleDateString('de-DE', {
          year: 'numeric',
          month: 'long',
        })
      }
    },
    blockedDays() {
      return new Set(
        this.existingDays
          .filter(day => !day.combining_dates)
          .map(day => new Date(day.date).toISODate())
      )
    },
    blockedMonths() {
      return new Set(
        this.existingDays
          .filter(day => day.combining_dates)
          .map(day => new Date(day.date).toISOMonth())
      )
    }
  },
  methods: {
    // Löscht den Tag und alle zugehörigen Meals
    deleteDay() {
      this.axios.delete(`invoice-days/${this.day.id}/`)
        .then(() => {
          // Optional: Emitte ein Event, wenn ein Tag gelöscht wurde
          this.$emit('update');
        })
        .catch(error => {
          console.error("Fehler beim Löschen des Tages:", error);
        });
    },
    // updateMeal wird via onBlur der Meal-Felder aufgerufen
    updateMeal(meal) {
      console.log('updateMeal', meal);
      // Prüfe, ob alle erforderlichen Felder im newMeal gesetzt sind
      if (meal.name && meal.price) {
        // Falls der Tag noch keine id besitzt, muss er zuerst angelegt werden
        if (!this.day.id) {
          console.log("keine id")
          // Falls day.customer noch nicht gesetzt ist, übernehmen wir den Kunden
          if (!this.day.customer && this.customer && this.customer.id) {
            this.day.customer = this.customer.id;
          }
          // Formatieren des Datums (nur Datum, ohne Uhrzeit)
          const formattedDate = new Date(this.day.date).toISOString().split('T')[0];
          this.day.date = formattedDate;
          this.axios.post('invoice-days/', this.day)
            .then(response => {
              console.log("tag gespeichert")
              // Setze die zurückgegebene ID in den day
              this.day.id = response.data.id
              console.log("jetzt versuchen wirs noch mal")
              this.updateMeal(meal)
              // Optional: Emitte ein Event, wenn ein neuer Tag erstellt wurde
              this.$emit('new-day-created', this.day);
            })
        } else {

          if (!meal.day) {
            meal.day = this.day.id
          }

          if (meal.id) {

            // Meal löschen, wenn count 0 ist
            if(meal.count === 0) {
              this.axios.delete(`invoice-meals/${meal.id}/`)
                .then(() => {
                  if (this.day.meals.length === 1) {
                    this.deleteDay();
                  } else { this.loadMeals(); }
                })
            } else {
              // Meal existiert bereits – Update via PATCH
              this.axios.patch(`invoice-meals/${meal.id}/`, meal)
                .then(() => {
                  this.loadMeals();
                })
            }

          } else {

            // Neues Meal – per POST erstellen
            this.axios.post('invoice-meals/', meal)
              .then(() => {
                // Nach erfolgreichem Speichern das newMeal-Formular zurücksetzen
                this.newMeal = { name: '', count: 1, price: '', delivered: false };
                this.$emit('update');
              })
          }
        }
      }
    },
    // Lädt die aktuelle Liste der Meals für den Tag über die Action im InvoiceDayViewSet
    loadMeals() {
      this.axios.get(`invoice-days/${this.day.id}/meals/`)
        .then(response => {
          // Aktualisiere den Tag mit der neuen Liste der Meals
          this.$set(this.day, 'meals', response.data);
        })
    },
    // addToDay und subtractFromDay werden nur im Template aufrufbar, wenn day noch keine id hat
    addToDay() {
      let newDate = new Date(this.day.date)
      if (this.day.combining_dates) {
        newDate.setMonth(newDate.getMonth() + 1)
      } else {
        newDate.setDate(newDate.getDate() + 1)
      }
      this.day.date = this.checkDate(newDate)
    },
    subtractFromDay() {
      let newDate = new Date(this.day.date)
      if (this.day.combining_dates) {
        newDate.setMonth(newDate.getMonth() - 1)
      } else {
        newDate.setDate(newDate.getDate() - 1)
      }
      this.day.date = this.checkDate(newDate, false)
    },
    checkDate(date, plus=true) {
      let ownMonth = date.toISOMonth()
      let ownDate = date.toISODate()
      const direction = plus ? 1 : -1

      // check if ownMonth or ownDate is in blockedTimes
      // while this is true add a day to the date
      while (this.blockedTimes.find(time => time === ownMonth || time === ownDate)) {
        if (this.day.combining_dates) {
          date.setMonth(date.getMonth() + direction)
        } else {
          date.setDate(date.getDate() + direction)
        }
        ownMonth = date.toISOMonth()
        ownDate = date.toISODate()
      }
      return date
    },
    toggleCombiningDates(day) {
      day.combining_dates = !day.combining_dates;
    },
    toggleDelivered() {
      // Wenn der Tag auf delivered gesetzt wird, sorgt der computed setter dafür, dass alle Meals ebenfalls delivered true sind
      this.allMealsDelivered = !this.day.delivered;
    },
    toggleMealDelivered(meal) {
      meal.delivered = !meal.delivered;
    }
  },
  created () {
    let newDate = new Date(this.day.date)
    this.day.date = this.checkDate(newDate)
  }
};
</script>

<style scoped lang="sass">
.meals
  padding: 12px 0
.v-btn.delivery
  color: lightgray

.v-btn.delivery.delivered
  color: green

.spacer-delivered
  width: 48px
</style>
