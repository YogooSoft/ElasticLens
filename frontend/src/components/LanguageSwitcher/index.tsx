import React from 'react';
import { Dropdown, Button } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { supportedLanguages } from '../../i18n/config';
import './styles.css';

export const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  
  const currentLang = supportedLanguages.find(
    lang => lang.code === i18n.language
  ) || supportedLanguages[0];

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
    localStorage.setItem('i18nextLng', langCode);
  };

  const menuItems = supportedLanguages.map(lang => ({
    key: lang.code,
    label: (
      <div className="language-option">
        <span className="flag">{lang.flag}</span>
        <span className="name">{lang.name}</span>
      </div>
    ),
    onClick: () => handleLanguageChange(lang.code)
  }));

  return (
    <Dropdown menu={{ items: menuItems }} placement="bottomRight">
      <Button 
        icon={<GlobalOutlined />} 
        className="language-switcher"
      >
        {currentLang.flag} {currentLang.name}
      </Button>
    </Dropdown>
  );
};
