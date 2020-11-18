import {useRef, useState} from "react";
import MonacoEditor from "./MonacoEditor";
import styles from '../styles/EditorTabs.module.css'


export default function EditorTabs() {
  const [value, setValue] = useState(["..."]);
  const [currTab, setCurrTab] = useState(0);
  const [tabCount, setTabCount] = useState(0);
  const [lang, setLang] = useState(Array(5).fill('none'))

  for(let i = 0; i < 5; i++) {
      EditorTabs[`editorDiv-${i}`] = useRef()
  }

  function onMount(_, editor) {
      setTabCount( tabCount + 1)
  }

  return (
    <>
        <div>
      <div className={styles.tabsContainer}>

          {value.map((v, i) => (
              <div
                  onClick={() => setCurrTab(i)}
                  className={currTab === i ? styles.tabsSelected : styles.tabs}
                  onKeyDown={(e) => {
                      const button = e.currentTarget

                      if(e.code == 'Enter') {
                          button.blur()  // Lose focus...
                      }
                  }}
                  onBlur={(e) => {
                      const filename = e.currentTarget.children[0]

                      if(filename.textContent === '') {
                          filename.textContent = `file_${i}`
                      }

                      if(filename.textContent.endsWith(".py")) {
                          let langCopy = [...lang]
                          langCopy[currTab] = 'python'

                          setLang(langCopy)
                      }
                  }}

              >
                  <text
                      contentEditable={true}
                      className={styles.tabsFilename}
                      onKeyDown={(e) => {
                          if(e.code === 'Enter') {
                              e.preventDefault()
                              e.currentTarget.blur()
                          }
                      }}
                  >file_{i}
                  </text>
                  <button
                      className={styles.tabsCloseButton}
                      onClick={(event) => {
                          let newValue = [...value];
                          let newLang = [...lang]
                          let newEditorDiv = EditorTabs[`editorDiv-${i - 1}`].current

                          newValue.splice(i, 1)
                          newLang[i] = "none"

                          setLang(newLang)
                          setValue(newValue);
                          setCurrTab(currTab - 1)
                          setTabCount(tabCount - 1)

                          newEditorDiv.style.display = "block"
                      }}
                  >X
                  </button>
              </div>
          ))}

      <button
          className={styles.tabsNew}
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
      </div>

      {value.map((v, i) => (
        <div
          style={{
            display: currTab === i ? "block" : "none",
          }}
          className={'maxed'}
          ref={EditorTabs[`editorDiv-${i}`]}
        >
          <MonacoEditor
            onMount={onMount}
            value={value[i]}
            language={lang[i]}
            onChange={(ev, newVal) => {
              let newValue = [...value];
              newValue[i] = newVal;
              setValue(newValue);
            }}
            theme={"mystBinDark"}
          />
        </div>
      ))}

      </div>
    </>
  );
}
