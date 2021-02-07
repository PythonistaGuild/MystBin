import { Nav, Navbar, OverlayTrigger, Popover, Toast } from "react-bootstrap";
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
import LogoMinimalMain from "../public/LogoMinimalMain";
import { useRouter } from "next/router";
import pasteStore from "../stores/PasteStore";

export default function OptsBar() {
  const [currentModal, setCurrentModal] = useState(null);
  const [expiryValue, setExpiryValue] = useState([-1, -1, -1]);
  const router = useRouter();
  const [paste, setPaste] = useState(pasteStore.getPaste());
  const [saveSuccessToast, setSaveSuccessToast] = useState(null);

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
        alert("Bookmark thing.");
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
        let files = [];

        for (let file of paste) {
          files.push({ filename: file["title"], content: file["content"] });
        }

        fetch("https://api-staging.mystb.in/paste", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ files: files }),
        })
          .then((r) => {
            if (r.status === 200) {
              return r.json();
            }
            console.error(r.status);
          })
          .then(async (d) => {
            if (d && d.id) {
              let path = `/${d.id}`;
              navigator.clipboard.writeText(window.location.origin + path);
              router.push(path);
              setSaveSuccessToast(d.id);
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

  actions.forEach(({ callback, hotKey }) => {
    useHotkeys(hotKey, callback);
  });

  return (
    <>
      {currentModal && currentModal}
      <Navbar className="justify-content-center">
        <Nav className={styles.optsNavContainer}>
          <LogoMinimalMain className={styles.logoMinimal} />
          {personal.map(OptsButton)}
          <hr className={styles.navGap} />
          {actions.map(OptsButton)}
          <hr className={styles.navGap} />
          {opts.map(OptsButton)}
        </Nav>
      </Navbar>

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
    </>
  );
}

function OptsButton(obj: {
  title: string;
  content: string;
  icon: JSX.Element;
  callback: () => void;
  hotKey?: string;
  optional?: boolean;
}): JSX.Element {
  return (
    <OverlayTrigger
      key={`opt-${obj.title}`}
      placement={"right"}
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