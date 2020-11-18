import { useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from '../styles/EditorTabs.module.css'


export default function EditorTabs() {
  const [value, setValue] = useState(["// write here", "// write here"]);
  const [currTab, setCurrTab] = useState(0);

  const[tabCount, setTabCount] = useState(0);


  for(let i = 0; i < 5; i++) {
      const [lang, setLang] = useState('none')
      EditorTabs[`tabLanguage-${i}`] = lang
      EditorTabs[`setTabLanguage-${i}`] = setLang
    }

  function onMount(_, editor) {
      setTabCount( tabCount + 1)
  }

  return (
    <>
      <div className={styles.tabsContainer}>
      {value.map((v, i) => (
        <button contentEditable={true}
                onClick={() => setCurrTab(i)} className={ currTab === i ? styles.tabsSelected : styles.tabs }
                onKeyDown={(e) => {
                    const button = e.currentTarget

                    if(e.code == 'Enter') {
                        button.blur()  // Lose focus...

                        if(button.textContent === '') {
                            button.textContent = `File ${currTab}`
                        }

                        if(button.textContent.endsWith(".py")) {
                            EditorTabs[`setTabLanguage-${currTab}`]('python')
                        }
                    }
                }}
        >File {i}</button>
      ))}
      <button
        onClick={() => {
          if (tabCount <= 4) {
          let newValue = [...value];
          newValue.push("");
          setValue(newValue);
          }
        }}
      >
        +
      </button>
      {value.map((v, i) => (
          i <= 4 ?
        <div
          style={{
            display: currTab === i ? "block" : "none",
          }}
          className={'maxed'}
        >
          <MonacoEditor
            onMount={onMount}
            value={value[i]}
            language={EditorTabs[`tabLanguage-${i}`]}
            onChange={(ev, newVal) => {
              let newValue = [...value];
              newValue[i] = newVal;
              setValue(newValue);
            }}
            theme={"mystBinDark"}
          />
        </div>
              :
              null
      ))}
      </div>
    </>
  );
}
