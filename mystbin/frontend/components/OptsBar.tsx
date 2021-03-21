import { OverlayTrigger, Popover, Spinner, Toast } from "react-bootstrap";
import React, { useEffect, useState } from "react";
import EnhancedEncryptionIcon from "@material-ui/icons/EnhancedEncryption";
import HourglassFullIcon from "@material-ui/icons/HourglassFull";
import SaveIcon from "@material-ui/icons/Save";
import EditIcon from "@material-ui/icons/Edit";
import FavoriteIcon from "@material-ui/icons/Favorite";
import styles from "../styles/OptsBar.module.css";
import { useHotkeys } from "react-hotkeys-hook";
import ExpiryModal from "./ExpiryModal";
import DashboardIcon from "@material-ui/icons/Dashboard";
import FiberNewIcon from "@material-ui/icons/FiberNew";
import BrushIcon from "@material-ui/icons/Brush";
import { useRouter } from "next/router";
import pasteStore from "../stores/PasteStore";
import LoginModal from "./LoginModal";
import cookieCutter from "cookie-cutter";
import ArrowUpwardIcon from "@material-ui/icons/ArrowUpward";
import ArrowDownwardIcon from "@material-ui/icons/ArrowDownward";
import { Slide } from "@material-ui/core";
import { LensTwoTone } from "@material-ui/icons";
import config from "../config.json";

export default function OptsBar() {
  const [currentModal, setCurrentModal] = useState(null);
  const [expiryValue, setExpiryValue] = useState([-1, -1, -1]);
  const router = useRouter();
  const [paste, setPaste] = useState(pasteStore.getPaste());
  const [saveSuccessToast, setSaveSuccessToast] = useState(null);
  const [saveBlankToast, setSaveBlankToast] = useState(false);
  const [saving, setSaving] = useState(false);
  const [optsVisible, setOptsVisible] = useState(true);
  useEffect(() => {
    pasteStore.addChangeListener(onChange);
    return () => pasteStore.removeChangeListener(onChange);
  }, []);
  function onChange() {
    setPaste(pasteStore.getPaste());
  }

  const personal = [
    {
      title: "Dashboard",
      content:
        "Login into your account via Discord, Google or GitHub and view your saved pastes and bookmarks or manage your preferences.",
      icon: <DashboardIcon />,
      callback: () => {
        const loginState = cookieCutter.get("state");

        if (loginState === "true") {
          router.push("/dashboard");
          return;
        }
        setCurrentModal(
          <LoginModal
            onHide={() => {
              setCurrentModal(null);
            }}
          />
        );
      },
    },

    {
      title: "Change Theme",
      content:
        "Change the look and feel of MystBin. Saves to your account preferences.",
      icon: <BrushIcon />,
    },

    {
      title: "Bookmark Paste",
      content: "Bookmark this paste to your favourites for later viewing.",
      icon: <FavoriteIcon />,
      callback: () => {
        if (!paste) {
          alert("Not a valid paste");
          return;
        }
        fetch(config["site"]["backend_site"] + "/users/bookmarks", {
          method: "PUT",
          headers: {
            Authorization: cookieCutter.get("token"),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ paste_id: paste.id }),
        }).then((value) => {
          if (value.status !== 201) {
            console.error(value.json()["error"]);
          } else {
            alert("Bookmark Saved!"); //TODO make this a pretty popup
          }
        });
      },
    },
  ];

  const actions = [
    {
      title: "New Paste",
      content: "Create a new paste to share.",
      icon: <FiberNewIcon />,
      callback: () => {
        router.push("/").then(() => {
          router.reload();
        });
      },
    },

    {
      title: "Save Paste",
      content: "Save this paste and all its files.",
      icon: <SaveIcon />,
      callback: () => {
        if (window.location.pathname !== "/") {
          return;
        }

        if (!paste) {
          return;
        }

        if (paste.length === 1 && paste[0]["content"] === "") {
          return setSaveBlankToast(true);
        }

        setSaving(true);
        let files = [];

        for (let file of paste) {
          files.push({ filename: file["title"], content: file["content"] });
        }

        fetch(config["site"]["backend_site"] + "/paste", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ files: files }),
        })
          .then((r) => {
            if (r.status === 200) {
              return r.json();
            }
            setSaving(false);
            console.error(r.status);
          })
          .then(async (d) => {
            if (d && d.id) {
              let path = `/${d.id}`;
              await navigator.clipboard.writeText(
                window.location.origin + path
              );
              // @ts-ignore
              router.push(path).then(setSaveSuccessToast(d.id));
              setSaving(false);
            }
          });
      },
      hotKey: "ctrl+s",
    },

    {
      title: "Edit Paste",
      content: "Copy and Edit this paste as a new paste.",
      icon: <EditIcon />,
      callback: () => {
        alert("test2!");
      },
      hotKey: "ctrl+e",
    },
  ];
  const opts = [
    {
      title: "Create Password",
      content: "Create a password for this paste and all its files.",
      optional: true,
      icon: <EnhancedEncryptionIcon />,
      callback: () => alert("test3"),
    },
    {
      title: "Create Expiry",
      content: "Create a expiry date for this paste and all its files.",
      optional: true,
      icon: <HourglassFullIcon />,
      callback: () => {
        setCurrentModal(
          <ExpiryModal
            initialValue={expiryValue}
            onHide={() => {
              setCurrentModal(null);
            }}
            onSubmit={setExpiryValue}
          />
        );
      },
    },
  ];
  function optionTitle() {
    return (optsVisible ? "Hide" : "Show") + " options";
  }
  function optionDescription() {
    return (optsVisible ? "Hide" : "Show") + " the options";
  }

  const collapse = [
    {
      title: optionTitle(),
      content: optionDescription(),
      icon: optsVisible ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />,
      callback: () => setOptsVisible(!optsVisible),
    },
  ];

  actions.forEach(({ callback, hotKey }) => {
    useHotkeys(hotKey, callback);
  });

  return (
    <>
      {currentModal && currentModal}
      <div>
        {optsVisible ? (
          <div></div>
        ) : (
          <div className={styles.optsNavContainerCollapsed}>
            {collapse.map(OptsButton)}
          </div>
        )}
        <Slide direction="down" in={optsVisible}>
          <div className={styles.optsNavContainer}>
            {personal.map(OptsButton)}
            <hr className={styles.navGap} />
            {actions.map(OptsButton)}
            <hr className={styles.navGap} />
            {opts.map(OptsButton)}
            {collapse.map(OptsButton)}
          </div>
        </Slide>
      </div>

      <Toast
        className={styles.saveSuccessToast}
        onClose={() => setSaveSuccessToast(null)}
        show={saveSuccessToast}
        delay={5000}
        autohide
      >
        <Toast.Header className={styles.saveSuccessToastHeader}>
          <strong className="mr-auto">Save Successful!</strong>
          <small>{saveSuccessToast}</small>
        </Toast.Header>
        <Toast.Body>Your paste URL has been copied to clipboard.</Toast.Body>
      </Toast>

      <Toast
        className={styles.saveBlankToast}
        onClose={() => setSaveBlankToast(false)}
        show={saveBlankToast}
        delay={5000}
        autohide
      >
        <Toast.Header className={styles.saveBlankToastHeader}>
          <strong className="mr-auto">Save Error!</strong>
        </Toast.Header>
        <Toast.Body>
          Your paste is empty, cannot save an empty paste.
        </Toast.Body>
      </Toast>
      <Spinner
        animation="border"
        variant="light"
        className={styles.saveSpinner}
        style={{ display: saving ? "block" : "none" }}
      />
    </>
  );
}

function OptsButton(obj: {
  title: string;
  content: string;
  icon: JSX.Element;
  callback: () => any;
  hotKey?: string;
  optional?: boolean;
}): JSX.Element {
  return (
    <OverlayTrigger
      key={`opt-${obj.title}`}
      placement={"left"}
      overlay={
        <Popover id={`opt-${obj.title}`} className={styles.popoverBody}>
          <Popover.Title className={styles.popoverHeader} as="h3">
            {obj.title}
            {obj.hotKey && (
              <span
                style={{
                  float: "right",
                  color: "rgba(255, 255, 255, .6)",
                }}
              >
                {obj.hotKey}
              </span>
            )}
          </Popover.Title>
          <Popover.Content>
            {obj.content}{" "}
            {obj.optional !== undefined && (
              <strong>{obj.optional ? "Optional" : "Required"}</strong>
            )}
          </Popover.Content>
        </Popover>
      }
    >
      <div className={styles.optsIconContainer} onClick={() => obj.callback()}>
        {obj.icon}
      </div>
    </OverlayTrigger>
  );
}
