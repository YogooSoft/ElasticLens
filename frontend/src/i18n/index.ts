import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { defaultLanguage } from './config';

// 导入中文语言资源
import zhCN_common from './locales/zh-CN/common.json';
import zhCN_home from './locales/zh-CN/home.json';
import zhCN_report from './locales/zh-CN/report.json';
import zhCN_history from './locales/zh-CN/history.json';
import zhCN_settings from './locales/zh-CN/settings.json';
import zhCN_upload from './locales/zh-CN/upload.json';
import zhCN_task from './locales/zh-CN/task.json';

// 导入繁体中文语言资源
import zhTW_common from './locales/zh-TW/common.json';
import zhTW_home from './locales/zh-TW/home.json';
import zhTW_report from './locales/zh-TW/report.json';
import zhTW_history from './locales/zh-TW/history.json';
import zhTW_settings from './locales/zh-TW/settings.json';
import zhTW_upload from './locales/zh-TW/upload.json';
import zhTW_task from './locales/zh-TW/task.json';

// 导入英文语言资源
import enUS_common from './locales/en-US/common.json';
import enUS_home from './locales/en-US/home.json';
import enUS_report from './locales/en-US/report.json';
import enUS_history from './locales/en-US/history.json';
import enUS_settings from './locales/en-US/settings.json';
import enUS_upload from './locales/en-US/upload.json';
import enUS_task from './locales/en-US/task.json';

// 导入日语语言资源
import jaJP_common from './locales/ja-JP/common.json';
import jaJP_home from './locales/ja-JP/home.json';
import jaJP_report from './locales/ja-JP/report.json';
import jaJP_history from './locales/ja-JP/history.json';
import jaJP_settings from './locales/ja-JP/settings.json';
import jaJP_upload from './locales/ja-JP/upload.json';
import jaJP_task from './locales/ja-JP/task.json';

// 导入法语语言资源
import frFR_common from './locales/fr-FR/common.json';
import frFR_home from './locales/fr-FR/home.json';
import frFR_report from './locales/fr-FR/report.json';
import frFR_history from './locales/fr-FR/history.json';
import frFR_settings from './locales/fr-FR/settings.json';
import frFR_upload from './locales/fr-FR/upload.json';
import frFR_task from './locales/fr-FR/task.json';

// 导入德语语言资源
import deDE_common from './locales/de-DE/common.json';
import deDE_home from './locales/de-DE/home.json';
import deDE_report from './locales/de-DE/report.json';
import deDE_history from './locales/de-DE/history.json';
import deDE_settings from './locales/de-DE/settings.json';
import deDE_upload from './locales/de-DE/upload.json';
import deDE_task from './locales/de-DE/task.json';

// 导入俄语语言资源
import ruRU_common from './locales/ru-RU/common.json';
import ruRU_home from './locales/ru-RU/home.json';
import ruRU_report from './locales/ru-RU/report.json';
import ruRU_history from './locales/ru-RU/history.json';
import ruRU_settings from './locales/ru-RU/settings.json';
import ruRU_upload from './locales/ru-RU/upload.json';
import ruRU_task from './locales/ru-RU/task.json';

const resources = {
  'zh-CN': {
    common: zhCN_common,
    home: zhCN_home,
    report: zhCN_report,
    history: zhCN_history,
    settings: zhCN_settings,
    upload: zhCN_upload,
    task: zhCN_task
  },
  'zh-TW': {
    common: zhTW_common,
    home: zhTW_home,
    report: zhTW_report,
    history: zhTW_history,
    settings: zhTW_settings,
    upload: zhTW_upload,
    task: zhTW_task
  },
  'en-US': {
    common: enUS_common,
    home: enUS_home,
    report: enUS_report,
    history: enUS_history,
    settings: enUS_settings,
    upload: enUS_upload,
    task: enUS_task
  },
  'ja-JP': {
    common: jaJP_common,
    home: jaJP_home,
    report: jaJP_report,
    history: jaJP_history,
    settings: jaJP_settings,
    upload: jaJP_upload,
    task: jaJP_task
  },
  'fr-FR': {
    common: frFR_common,
    home: frFR_home,
    report: frFR_report,
    history: frFR_history,
    settings: frFR_settings,
    upload: frFR_upload,
    task: frFR_task
  },
  'de-DE': {
    common: deDE_common,
    home: deDE_home,
    report: deDE_report,
    history: deDE_history,
    settings: deDE_settings,
    upload: deDE_upload,
    task: deDE_task
  },
  'ru-RU': {
    common: ruRU_common,
    home: ruRU_home,
    report: ruRU_report,
    history: ruRU_history,
    settings: ruRU_settings,
    upload: ruRU_upload,
    task: ruRU_task
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: defaultLanguage,
    lng: localStorage.getItem('i18nextLng') || defaultLanguage,
    debug: process.env.NODE_ENV === 'development',
    
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  });

export default i18n;
