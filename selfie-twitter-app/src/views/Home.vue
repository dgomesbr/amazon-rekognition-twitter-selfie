<template>
  <div class="q-pa-md row q-gutter-md">    
    <div v-for="selfie in processedSelfies" :key="selfie.face_id + selfie.etype">
      <SelfieCard :selfie="selfie">
      </SelfieCard>
    </div>
  </div>
</template>

<script>
import SelfieCard from "../components/SelfieCard";

export default {
  name: "home",
  components: {
    SelfieCard
  },
  data() {
    return {
      baseUrl: process.env.VUE_APP_AWS_API_URL,
      selfies: []
    };
  },
  beforeMount() {
    this.getSelfies();
  },
  methods: {
    getSelfies() {
      try {
        //console.log(this.baseUrl)
        this.$http.get(this.baseUrl + "/selfies").then(results => {
          this.selfies = results.data;
        });
      } catch (error) {
        console.error(error);
        this.$q.notify({
          color: "negative",
          position: "top",
          icon: "warning",
          message: "Something went wrong: " + error
        });
      }
    },
  },
  computed: {
    processedSelfies() {
      return this.selfies;
    }
  }
};
</script>
