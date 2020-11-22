import Head from "next/head";
import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";
import {PropsWithoutRef} from "react";
import {GetServerSideProps} from "next";

const PostMonacoEditor = dynamic(() => import("../components/EditorTabs"), {
  ssr: false,
});

export default function Home(props: PropsWithoutRef<{ password, initialData, dummyData }>) {
  const { password, initialData, dummyData } = props;

  return (
    <div>
      <Head>
        <title>MystBin</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Base className={styles.Tabs}>
        <PostMonacoEditor password={password} initialData={initialData} dummyData={dummyData} />
      </Base>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  const password =  "abc";
  let initialData;
  let dummyData = [{title: "test.py", content: "print('Hello World!')"}, {title: "other.py", content: "print('other.py')"}];

  if(password) {
    initialData = [{title: "!protected!", content: "Password protected paste."}];
  }
  else {
    initialData = dummyData;
  }

  return {
    props: {
      password,
      initialData,
      dummyData,
    },
  }
}