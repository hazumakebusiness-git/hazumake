// Firebase config for Hazumake
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyCAjt8cq8pvbkhc-FeKAUb6GtcwCwZahQc",
  authDomain: "hazumakestore.com",
  projectId: "hazumake",
  storageBucket: "hazumake.firebasestorage.app",
  messagingSenderId: "1098202035178",
  appId: "1:1098202035178:web:19b12d390912d8c3897893",
  measurementId: "G-6FTCG8DTLB"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
