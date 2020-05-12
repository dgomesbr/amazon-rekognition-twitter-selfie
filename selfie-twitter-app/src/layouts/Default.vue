<template>
  <q-layout view="hHh lpR fFf">
    <q-header bordered class="bg-primary text-white" height-hint="98">
      <q-toolbar>
        <q-btn flat round dense icon="house" class="q-mr-sm" />
        <q-separator dark vertical inset />
        <q-btn stretch flat label="Run Athena Query" @click="athQuery"/>
        <div v-if="isAthRunning">
        <q-spinner-audio
          color="primary"
          size="2em"
        />
        <q-tooltip :offset="[0, 8]">QSpinnerAudio</q-tooltip>
        </div>
        <q-toolbar-title>Twitter Selfie Demo</q-toolbar-title> <span caption>Rank from the last 7 days</span>
      </q-toolbar>
      <q-banner class="bg-orange text-white">
        Twitter is a public platform that does not moderate photos uploaded by its users. This demo uses the AWS Reckognition feature, but from occasionally inappropriate photos can appear. Please use the delete icon to remove these photos from the database.    
    </q-banner>
    </q-header>

    <q-page-container>
      <router-view />      
    </q-page-container>
  </q-layout>
</template>

<script>
const baseUrl = "https://hkaq3l76j1.execute-api.us-west-2.amazonaws.com";

export default {
  data() {
    return {
        isAthRunning: false
    };
  },
  methods: {
    async athQuery() {
      try {
        console.log("running athQuery");
        this.isAthRunning = true
        let res = await this.$http.get(baseUrl + '/athdispatch')
        console.log(res)
        this.$q.notify({
          color: "accent",
          position: "top",
          icon: "info",
          message: "Query submitted. Please refresh this page in 30s"
        });
      } catch (error) {
        console.error(error);
        this.isAthRunning = false
        this.$q.notify({
          color: "negative",
          position: "top",
          icon: "warning",
          message: "Something went wrong: " + error
        });
      }
    },
  }
};
</script>


