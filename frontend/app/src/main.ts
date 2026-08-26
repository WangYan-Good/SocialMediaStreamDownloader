import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { bootstrapApplication } from './bootstrap'
import router from './router'
import './styles/global.css'

void bootstrapApplication(createApp(App), createPinia(), router, '#app')
