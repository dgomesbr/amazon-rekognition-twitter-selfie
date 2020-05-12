<template>
  <div>
    <q-card class="my-card" v-if="selfie.face_id">
      <q-item>
        <q-item-section>
          <q-item-label>{{ selfie.etype }} - Score: {{ selfie.confidence }}</q-item-label>
          <q-item-label
            caption
          >{{ selfie.first_name }} {{ selfie.last_name }} - Age {{ selfie.age }} - Gender {{ selfie.gender_value}}</q-item-label>
          <q-item-label caption>Updated at {{ selfie.updated_at }}</q-item-label>
        </q-item-section>
      </q-item>
      <q-card-section>
        <canvas
          :id="'canvas_' + selfie.face_id + '_' + selfie.etype"
        />
        <q-card-actions>
          <q-btn flat color="red" icon="delete" @click="delSelfie(selfie.face_id,selfie.etype)" />
        </q-card-actions>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
const baseUrl = "https://hkaq3l76j1.execute-api.us-west-2.amazonaws.com";

export default {
  props: {
    selfie: {}
  },
  mounted() {
    this.renderImages(this.selfie);
  },
  methods: {
    renderImages(selfie) {
      try {
        let id = "canvas_" + selfie.face_id + "_" + selfie.etype;
        //console.log(id);

        let scale = 500 / selfie.imgWidth;

        let box_left = Math.round(selfie.bbox_left * scale);
        let box_top = Math.round(selfie.bbox_top * scale);
        let box_width = Math.round(selfie.bbox_width * scale);
        let box_height = Math.round(selfie.bbox_height * scale);

        let newImageHeight = Math.round(
          (selfie.imgHeight / selfie.imgWidth) * 500
        );

        // console.log('img W:' +  selfie.imgWidth + ' H:' + selfie.imgHeight)
        // console.log('img adjusted W: 500 H:' + newImageHeight)
        // console.log('box L:' +  selfie.bbox_left + ' P:' + selfie.bbox_top + ' W:' +  selfie.bbox_width + ' H:' + selfie.bbox_height )
        // console.log('box adjusted L:' +  box_left + ' P:' + box_top + ' W:' +  box_width + ' H:' + box_height )

        // var canvas = document.createElement("canvas");
        // canvas.setAttribute("id", id);
        var canvas = document.getElementById(id);
        var context = canvas.getContext("2d");

        var img = new Image();
        img.onload = function() {
          canvas.width = 500;
          canvas.height = (selfie.imgHeight / selfie.imgWidth) * 500;
          context.drawImage(
            img,
            0,
            0,
            selfie.imgWidth,
            selfie.imgHeight,
            0,
            0,
            500,
            newImageHeight
          );
          context.lineWidth = 3;
          context.beginPath();
          context.rect(
            Math.round(box_left),
            Math.round(box_top),
            Math.round(box_width),
            Math.round(box_height)
          );
          context.strokeStyle = "green";
          context.stroke();
        };
        img.src = selfie.image_url;
      } catch (e) {
        console.error(e);
      }
    },
    delSelfie(id, emotion) {
      console.log("del: " + id + " " + emotion);
      try {
        console.log("running Axios");
        this.$http
          .post(baseUrl + "/delselfie", {
            id: id,
            emotion: emotion
          })
          .then(function(response) {
            console.log(response);
            var photo = document.getElementById('canvas_' + id + '_' + emotion);
            photo.remove(); 
          })
          .catch(function(error) {
            console.error(error);
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
    }
  }
};
</script>